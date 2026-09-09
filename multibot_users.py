from __future__ import annotations
import asyncio, os, re, time
from typing import Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
except Exception:
    AsyncIOMotorClient = None

from pyrogram.errors import ChatWriteForbidden, FloodWait, InputUserDeactivated, PeerIdInvalid, UserIsBlocked

MONGO_URI = os.getenv("MONGO_URI", "").strip()
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "viralbots").strip()
MONGO_USERS_COLLECTION = os.getenv("MONGO_USERS_COLLECTION", "multi_bot_users").strip()
BOT_KEY = ""
BOT_KEY_SAFE = ""
BOT_USERNAME = ""
BOT_ID = 0

def _parse_owner_ids() -> set[int]:
    ids = set()
    raw = os.getenv("OWNER_CHAT_ID", "").strip()
    if raw.lstrip("-").isdigit():
        ids.add(int(raw))
    for part in re.split(r"[,;\s]+", os.getenv("OWNER_CHAT_IDS", "").strip()):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids

OWNER_CHAT_IDS = _parse_owner_ids()
USER_GONE_ERRORS = (UserIsBlocked, InputUserDeactivated, PeerIdInvalid, ChatWriteForbidden)
_client = None
_mongo_client = None; _mongo_db = None; _users_col = None
_memory_users: set[int] = set()
_broadcast_jobs: dict[str, Any] = {}

def _safe_field(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", (value or "").strip().lstrip("@"))
    return cleaned or "unknown_bot"

def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

async def init_multibot(client) -> None:
    global _client, BOT_KEY, BOT_KEY_SAFE, BOT_USERNAME, BOT_ID
    global _mongo_client, _mongo_db, _users_col
    _client = client
    me = await client.get_me()
    BOT_USERNAME = getattr(me, "username", "") or ""
    BOT_ID = int(getattr(me, "id", 0) or 0)
    BOT_KEY = BOT_USERNAME or str(BOT_ID)
    BOT_KEY_SAFE = _safe_field(BOT_KEY)
    if not MONGO_URI or AsyncIOMotorClient is None:
        return
    _mongo_client = AsyncIOMotorClient(MONGO_URI)
    _mongo_db = _mongo_client[MONGO_DB_NAME]
    _users_col = _mongo_db[MONGO_USERS_COLLECTION]
    await _users_col.create_index("user_id", unique=True)
    await _users_col.create_index(f"bots.{BOT_KEY_SAFE}.last_seen_at")
    await _users_col.create_index("bot_keys")

async def save_user(user_id: int, username: str = "", first_name: str = "", last_name: str = "") -> None:
    if not user_id: return
    if _users_col is None:
        _memory_users.add(int(user_id)); return
    now = _utc_now()
    await _users_col.update_one(
        {"user_id": int(user_id)},
        {"$set": {"user_id": int(user_id), "username": username, "first_name": first_name, "last_name": last_name, "updated_at": now,
                  f"bots.{BOT_KEY_SAFE}.bot_key": BOT_KEY, f"bots.{BOT_KEY_SAFE}.bot_username": BOT_USERNAME,
                  f"bots.{BOT_KEY_SAFE}.bot_id": BOT_ID, f"bots.{BOT_KEY_SAFE}.last_seen_at": now},
         "$setOnInsert": {"created_at": now}, "$addToSet": {"bot_keys": BOT_KEY}},
        upsert=True)

async def save_user_from_message(message) -> None:
    user = getattr(message, "from_user", None)
    if user is None: return
    await save_user(int(user.id), username=getattr(user, "username", None) or "",
                    first_name=getattr(user, "first_name", None) or "", last_name=getattr(user, "last_name", None) or "")

async def remove_user_for_this_bot(user_id: int) -> None:
    if _users_col is None:
        _memory_users.discard(int(user_id)); return
    await _users_col.update_one({"user_id": int(user_id)},
        {"$unset": {f"bots.{BOT_KEY_SAFE}": ""}, "$pull": {"bot_keys": BOT_KEY}, "$set": {"updated_at": _utc_now()}})
    doc = await _users_col.find_one({"user_id": int(user_id)}, {"bot_keys": 1})
    if doc and not doc.get("bot_keys"):
        await _users_col.delete_one({"user_id": int(user_id)})

async def count_users_for_this_bot() -> int:
    if _users_col is None: return len(_memory_users)
    return await _users_col.count_documents({f"bots.{BOT_KEY_SAFE}.last_seen_at": {"$exists": True}})

async def iter_users_for_this_bot():
    if _users_col is None:
        for uid in list(_memory_users): yield uid; return
    query = {f"bots.{BOT_KEY_SAFE}.last_seen_at": {"$exists": True}}
    page_size = 500; last_id = None
    while True:
        page_query = dict(query)
        if last_id is not None: page_query["_id"] = {"$gt": last_id}
        docs = await (_users_col.find(page_query, {"_id": 1, "user_id": 1}).sort("_id", 1).limit(page_size).to_list(length=page_size))
        if not docs: return
        for doc in docs:
            last_id = doc["_id"]; yield int(doc["user_id"])
        if len(docs) < page_size: return

async def handle_broadcast_command(client, message) -> bool:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in OWNER_CHAT_IDS: return False
    if _broadcast_jobs:
        await message.reply("⚠️ Broadcast already running."); return True
    reply = message.reply_to_message
    payload = ""
    if message.text and message.text.startswith("/broadcast"):
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1: payload = parts[1].strip()
    if reply is not None: source = {"type": "copy", "message": reply}
    elif payload: source = {"type": "text", "text": payload}
    else:
        await message.reply("📣 Reply to a post with /broadcast, or use /broadcast your message."); return True
    total = await count_users_for_this_bot()
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel Broadcast", callback_data=f"cancel_broadcast:pending")]])
    status = await message.reply(f"🚀 Broadcast starting\n\n🤖 Bot: @{BOT_USERNAME or BOT_KEY}\n👥 Users: {total}", reply_markup=kb)
    asyncio.create_task(run_broadcast(message.chat.id, status.id, source))
    return True

async def run_broadcast(admin_chat_id: int, status_message_id: int, source: dict) -> None:
    job_id = str(status_message_id)
    cancel_event = asyncio.Event()
    stats = {"started_at": int(time.time()), "total": await count_users_for_this_bot(), "done": 0, "sent": 0, "failed": 0, "deleted": 0, "cancelled": 0}
    _broadcast_jobs[job_id] = {"cancel": cancel_event, "stats": stats}
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    def kb(jid): return InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Cancel Broadcast", callback_data=f"cancel_broadcast:{jid}")]])
    def txt(s, r=True):
        if s.get("cancelled"): st = "🛑 Broadcast cancelled"
        elif r: st = "🚀 Broadcast running"
        else: st = "✅ Broadcast finished"
        speed = max(0.1, s["done"] / max(1, time.time() - s["started_at"]))
        return f"{st}\n\n👥 Total: {s['total']}\n📨 Done: {s['done']}\n✅ Sent: {s['sent']}\n❌ Failed: {s['failed']}\n🗑 Deleted: {s['deleted']}\n⚡ Speed: {speed:.1f}/sec"
    last_edit = 0.0
    try:
        try: await _client.edit_message_text(chat_id=admin_chat_id, message_id=status_message_id, text=txt(stats, True), reply_markup=kb(job_id))
        except Exception: pass
        async for user_id in iter_users_for_this_bot():
            if cancel_event.is_set(): stats["cancelled"] = 1; break
            try:
                if source["type"] == "copy": await _client.send_message(user_id, source["message"])
                else: await _client.send_message(user_id, source["text"])
                stats["sent"] += 1
            except FloodWait as exc:
                await asyncio.sleep(exc.value)
                try:
                    if source["type"] == "copy": await _client.send_message(user_id, source["message"])
                    else: await _client.send_message(user_id, source["text"])
                    stats["sent"] += 1
                except Exception as retry_exc:
                    stats["failed"] += 1
                    if isinstance(retry_exc, USER_GONE_ERRORS): await remove_user_for_this_bot(user_id); stats["deleted"] += 1
            except Exception as exc:
                stats["failed"] += 1
                if isinstance(exc, USER_GONE_ERRORS): await remove_user_for_this_bot(user_id); stats["deleted"] += 1
            stats["done"] += 1
            now = time.time()
            if now - last_edit >= 2 or stats["done"] == stats["total"]:
                last_edit = now
                try: await _client.edit_message_text(chat_id=admin_chat_id, message_id=status_message_id, text=txt(stats, True), reply_markup=kb(job_id))
                except Exception: pass
            await asyncio.sleep(0.04)
    finally:
        _broadcast_jobs.pop(job_id, None)
        try: await _client.edit_message_text(chat_id=admin_chat_id, message_id=status_message_id, text=txt(stats, False))
        except Exception: pass

async def handle_cancel_callback(client, callback_query) -> bool:
    data = callback_query.data or ""
    if not data.startswith("cancel_broadcast:"): return False
    user_id = callback_query.from_user.id if callback_query.from_user else 0
    if user_id not in OWNER_CHAT_IDS:
        try: await callback_query.answer("Only admin can cancel.", show_alert=True)
        except Exception: pass; return True
    job_id = data.split(":", 1)[1]
    if job_id == "pending":
        try: await callback_query.answer("Starting...")
        except Exception: pass; return True
    job = _broadcast_jobs.get(job_id)
    if job: job["cancel"].set()
    try: await callback_query.answer("🛑 Cancelling...")
    except Exception: pass
    return True

async def handle_status_command(client, message) -> bool:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in OWNER_CHAT_IDS: return False
    await message.reply(f"📊 Users started for @{BOT_USERNAME or BOT_KEY}: {await count_users_for_this_bot()}")
    return True

async def handle_stats_command(client, message) -> bool:
    user_id = message.from_user.id if message.from_user else 0
    if user_id not in OWNER_CHAT_IDS: return False
    await message.reply(f"📊 Users for @{BOT_USERNAME or BOT_KEY}: {await count_users_for_this_bot()}\n🔑 Bot key: {BOT_KEY_SAFE}\n💾 Storage: {'mongo' if _users_col is not None else 'memory'}")
    return True
