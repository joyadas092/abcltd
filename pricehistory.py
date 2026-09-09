from pyrogram import Client, filters, enums
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import errors
from pyrogram.enums import ChatAction

import tempfile
from quart import Quart
from functions import *
import os
from dotenv import load_dotenv
from ban_manager import is_banned
from multibot_users import (
    handle_broadcast_command,
    handle_cancel_callback,
    handle_status_command,
    handle_stats_command,
    init_multibot,
    save_user_from_message,
)
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
admin_chat_id = 849188964
auth_channel_env = int(os.getenv("AUTH_CHANNEL", "-1003849048564") or -1003849048564)
AUTH_CHANNEL = auth_channel_env
AUTH_CHANNEL_URL = os.getenv("AUTH_CHANNEL_URL", "https://t.me/+nHzi25ZLNlE4MjJl").strip()
DealerID = ['5886397642', '-1002060929372', '-4247871412']
Target_Channel_id = int(os.getenv("TARGET_CHANNEL_ID", "-1002038980148") or -1002038980148)
# Define a handler for the /start command
bot = Quart(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@bot.route('/')
async def hello():
    return 'Hello, world!'


async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        return False
    except PeerIdInvalid:
        # AUTH_CHANNEL peer not cached yet (fresh/missing session) — resolve once and retry.
        try:
            await bot.get_chat(AUTH_CHANNEL)
            user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
        except UserNotParticipant:
            return False
        except Exception as e:
            logger.error(f"[is_subscribed] retry after PeerIdInvalid failed: {e}")
            return False
    except Exception as e:
        logger.error(f"[is_subscribed] unexpected error: {e}")
        return False
    return user.status != enums.ChatMemberStatus.BANNED


@app.on_message(filters.command("start") & (filters.group | filters.private) & filters.incoming)
async def start(app, message):
    bot_info = await app.get_me()
    bot_username = bot_info.username
    if message.chat.type == enums.ChatType.PRIVATE:
        await save_user_from_message(message)
    if len(message.command) > 1:
        product_id = message.command[1]
        # print(product_id)
        await app.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

        url = f'https://www.amazon.in/dp/{product_id}'
        product_name, imageUrl, Price = await get_product_details(url)

        keepa_url, amazon_url, affiliate_url = keepa_process(url)

        combined_image = await merge_images([imageUrl, keepa_url])
        if combined_image:
            image_bytes = BytesIO()
            combined_image.save(image_bytes, format='JPEG')
            image_bytes.seek(0)
            await app.send_photo(message.chat.id, photo=image_bytes,
                                 caption=f"Product: {product_name}\n\nCurrent Price: <b>{Price}</b>\n\nBEST BUY LINK: <b>{affiliate_url}</b>\n\nfrom <b>@PriceGraph </b>",
                                 reply_markup=Promo2)
        else:
            await app.send_message(message.chat.id,
                                   f"Product: {product_name}\n\nCurrent Price: <b>{Price}</b>\n\nBEST BUY LINK: <b>{affiliate_url}</b>\n\nfrom <b>@PriceGraph </b>",
                                   reply_markup=Promo2)

    else:
        await app.send_chat_action(message.chat.id, ChatAction.TYPING)
        await app.send_message(
            message.chat.id,
            f"<b>Hey! I am {bot_username}.\n\n➡️ Just send me a valid Amazon.in product link. I will share the Price History Graph of the last 3 months😍😍\n\nBuy when the Price is Low📉\n\n<a href='https://t.me/Loots_Xpert/12'>👉 CLICK HERE TO SEE TUTORIAL 👈</a></b>",
            disable_web_page_preview=True
        )  # Check if the message is in a group

    # Check if the message is in a group

    # if message.chat.type== enums.ChatType.PRIVATE:
    #     await message.reply(
    #         "Hey! Just send me a valid Amazon product link. I will share you the Price History Graph of last 3 months😍😍\n\nBuy when the Price is Low📉")


Promo = InlineKeyboardMarkup(
    [[InlineKeyboardButton("PriceHistory Bot 🤖", url="https://t.me/Amazon_Pricehistory_Bot"),
      InlineKeyboardButton("🛍️ ProductsFinder Bot", url="https://t.me/ProductsFinder_Bot")],
     [InlineKeyboardButton("🎁 Main Channel", url="https://t.me/+HeHY-qoy3vsxYWU1"),
      InlineKeyboardButton("🔔 Join 2.0", url="https://t.me/+mUXCQYrUiKg0NDQ1")]
     ])
Promo2 = InlineKeyboardMarkup(
    [[InlineKeyboardButton("MAXIMUM DEALS 🛒", url="https://t.me/addlist/6R2xTLIL9JFkMWI1")],
     [InlineKeyboardButton("🔔 Main Channel ", url="https://t.me/+HeHY-qoy3vsxYWU1"),
      InlineKeyboardButton("Whatsapp Loots 💬", url="https://t.me/Loots_Xpert/33")]])

forward_off = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Turn Off", callback_data='forward off')]])
forward_on = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Turn ON", callback_data='forward on')]])
global forward
forward = True

# =========================
# 📢 Promo Control (like divideraff.py)
# =========================
promo_enabled = False

PROMO_KEYBOARD = InlineKeyboardMarkup(
    [[InlineKeyboardButton("PriceHistory Bot 🤖", url="https://t.me/Amazon_Pricehistory_Bot"),
      InlineKeyboardButton("🛍️ ProductsFinder Bot", url="https://t.me/ProductsFinder_Bot")],
     [InlineKeyboardButton("🎁 Main Channel", url="https://t.me/+HeHY-qoy3vsxYWU1"),
      InlineKeyboardButton("🔔 Join 2.0", url="https://t.me/+mUXCQYrUiKg0NDQ1")]]
)
PROMO_FOOTER = "\n\n<b>🛍️ 👉 <a href='https://t.me/addlist/zzZb8Deuzy9kZjQ1'>Click here to Join All Deals</a></b>"


def promo_markup():
    return PROMO_KEYBOARD if promo_enabled else None


def promo_footer():
    return PROMO_FOOTER if promo_enabled else ""

# =========================
# 📌 Silent Control (like divideraff.py)
# =========================
silent_interval = 3
post_counter = {}

def should_notify(chat_id: int) -> bool:
    if chat_id not in post_counter:
        post_counter[chat_id] = 0
    post_counter[chat_id] += 1
    return post_counter[chat_id] % silent_interval == 0


@app.on_message(filters.command('forward') & filters.user(5886397642))
async def forwardtochannel(app, message):
    await message.reply(text='Forward Status', reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("Turn ON", callback_data='forward on')],
         [InlineKeyboardButton("Turn Off", callback_data='forward off')]])
                        )


@app.on_callback_query()
async def callback_query(app, CallbackQuery):
    global forward, promo_enabled, silent_interval
    data = CallbackQuery.data or ""

    if data in {"promo on", "promo off"} or data.startswith("silent "):
        user_id = CallbackQuery.from_user.id if CallbackQuery.from_user else None
        if user_id not in promo_admin_ids:
            await CallbackQuery.answer("Not allowed", show_alert=True)
            return

        if data == "promo on":
            promo_enabled = True
            await CallbackQuery.edit_message_text("Promo ON ✅", reply_markup=promo_off_kb)
            await CallbackQuery.answer("Promo ON")
            return
        if data == "promo off":
            promo_enabled = False
            await CallbackQuery.edit_message_text("Promo OFF 🚫", reply_markup=promo_on_kb)
            await CallbackQuery.answer("Promo OFF")
            return

        try:
            interval = int(data.split(maxsplit=1)[1])
        except (IndexError, ValueError):
            await CallbackQuery.answer("Invalid silent interval", show_alert=True)
            return
        if interval not in {2, 3, 5, 10}:
            await CallbackQuery.answer("Invalid silent interval", show_alert=True)
            return

        silent_interval = interval
        await CallbackQuery.edit_message_text(
            f"Silent: notify every {silent_interval} posts."
        )
        await CallbackQuery.answer(f"Silent {silent_interval}")
        return

    if await handle_cancel_callback(app, CallbackQuery):
        return
    if data == 'forward off':
        await CallbackQuery.edit_message_text('Forward to Channel Status turned Off', reply_markup=forward_on)
        forward = False
    elif data == 'forward on':
        await CallbackQuery.edit_message_text('Forward to Channel Status turned On', reply_markup=forward_off)
        forward = True
    elif data == 'Send':
        a = CallbackQuery.message
        notify = should_notify(Target_Channel_id)
        if a.photo:
            await app.send_photo(
                chat_id=Target_Channel_id,
                photo=a.photo.file_id,
                caption=a.caption,
                caption_entities=a.caption_entities,
                reply_markup=promo_markup(),
                disable_notification=not notify,
            )
        else:
            await app.send_message(
                chat_id=Target_Channel_id,
                text=a.text or "",
                entities=a.entities,
                reply_markup=promo_markup(),
                disable_notification=not notify,
            )
        await CallbackQuery.answer(text='Sent to Channel✨', show_alert=True)



non_command_filter = filters.create(
    lambda _, __, message: not (message.text or message.caption or "").lstrip().startswith("/")
)


@app.on_message(
    ((filters.private & filters.incoming) | (filters.group & filters.incoming))
    & non_command_filter
)
async def handle_text(app, message):
    bot_info = await app.get_me()
    bot_username = bot_info.username
    user_id = message.from_user.id

    # 🚫 BAN CHECK (FIRST LINE)
    if is_banned(user_id):
        await message.reply("🚫 You are banned from using this bot.")
        return
    if message.chat.type == enums.ChatType.PRIVATE:
        await save_user_from_message(message)
    Join = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Join Channel", url=AUTH_CHANNEL_URL)]])

    # Ignore commands (promo, start, broadcast, stats, etc.) and non-product random text
    raw_text = (message.text or message.caption or "").strip()
    cmd_first = raw_text.split(maxsplit=1)[0].lower() if raw_text else ""
    if cmd_first.startswith("/"):
        return None
    # Ignore very short / emoji-only / non-letter noise
    if len(raw_text) < 2 or not any(ch.isalpha() for ch in raw_text):
        return None

    if AUTH_CHANNEL and not await is_subscribed(app, message):
        await app.send_message(message.chat.id,
                               '<b>Join Telegram Channel to Use this Bot 👇👇\n\nJOIN AND TRY AGAIN</b>',
                               reply_markup=Join)
        return

    try:
        if message.photo:
            text = message.caption if message.caption else message.text
            inputvalue = text
            # print(message.chat.id)
            if str(message.chat.id) in DealerID:
                # print('gg')
                hyperlinkurl = []
                for entity in message.caption_entities:
                    # new_entities.append(entity)
                    if entity.url is not None:
                        hyperlinkurl.append(entity.url)
                pattern = re.compile(r'Buy Now')

                inputvalue = pattern.sub(lambda x: hyperlinkurl.pop(0), inputvalue).replace('Regular Price', 'MRP').replace('- Sent via TeleFeed','').replace('• Sent via TeleFeed','').strip()
                if "😱 Deal Time" in inputvalue:
                    # Remove the part
                    inputvalue = inputvalue.split("😱 Deal Time")[0]
                # print(inputvalue)
        elif message.text:
            inputvalue = message.text
            if str(message.chat.id) in DealerID:
                # print('gg')
                hyperlinkurl = []
                for entity in message.entities:
                    # new_entities.append(entity)
                    if entity.url is not None:
                        hyperlinkurl.append(entity.url)
                pattern = re.compile(r'Buy Now')

                inputvalue = pattern.sub(lambda x: hyperlinkurl.pop(0), inputvalue).replace('Regular Price', 'MRP').replace('- Sent via TeleFeed','').replace('• Sent via TeleFeed','').strip()
                if "😱 Deal Time" in inputvalue:
                    # Remove the part
                    inputvalue = inputvalue.split("😱 Deal Time")[0]


    except Exception as e:
        # Handle exceptions
        await app.send_message(message.chat.id, f"Something went wrong: {str(e)}")
    # a = await app.send_message(message.chat.id, "Just wait 5 Seconds⏳⏳....Bot is Working🤖>>>>")
    try:
        if 'LivegramBot' in inputvalue or 'You cannot forward someone' in inputvalue or user_id in DealerID:
            await message.delete()
            return None
        extracted_link = extract_link_from_text(inputvalue)
        # print(extracted_link)
        a = await app.send_message(message.chat.id, "Just wait 5 Seconds⏳⏳....Bot is Working🤖>>>>")
        if not extracted_link:
            d = await app.send_message(message.chat.id, "Link not Found🫥🫥...")

            await a.delete()
            await d.delete()

            if message.chat.type == enums.ChatType.PRIVATE:
                await message.delete()
                e = await app.send_message(message.chat.id, "Searching Query in amazon.in...")

                search_result = amazon_in.search_items(keywords=inputvalue, item_count=6)
                # print(search_result)
                for item in search_result.items:
                    print(item)

                    response = requests.get(item.images.primary.large.url)
                    # print('gg')
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        image_bytes = BytesIO()
                        img.save(image_bytes, format='JPEG')
                        image_bytes.seek(0)

                    await app.send_photo(chat_id=message.chat.id, photo=image_bytes,
                                         caption=f"{item.item_info.title.display_value}\n\n Currrent Price : "
                                                 # f"{item.offers.listings[0].price.amount}",
                                                ,
                                         reply_markup=InlineKeyboardMarkup(
                                             [[InlineKeyboardButton("BUY NOW", url=f'{item.detail_page_url}')],
                                              [InlineKeyboardButton("CLICK to See Price History 📉",
                                                                    url=f'https://t.me/{bot_username}?start={item.asin}')]
                                              ]))
                    await e.delete()


            return None

        clean_url = remove_amazon_affiliate_parameters(unshorten_url(extracted_link))
        # print('clean url: '+clean_url)
        if 'amazon' in clean_url:
            country_code = extract_country_code(clean_url)
            product_name, imageUrl, Price = await get_product_details(clean_url)

            keepa_url, amazon_url, affiliate_url = keepa_process(clean_url)

            combined_image = await merge_images([imageUrl, keepa_url])

            if country_code == 'in':
                caption = (
                    f"Product: {product_name}\n\nCurrent Price: <b>{Price}</b>\n\n"
                    f"<b>You may get a CASHBACK!! Check Your Coupon Page Here👇👇 : \n\n"
                    f"🔗 https://amzn.to/3WMJyqy \n\nYour Product Link 👇👇:\n\n"
                    f"🔗{affiliate_url}\n\nfrom @PriceGraph </b>"
                )
            else:
                caption = (
                    f"Product: {product_name}\n\nCurrent Price: <b>{Price}</b>\n\n"
                    f"<b>Your Product Link 👇👇:\n\n"
                    f"🔗{affiliate_url}\n\nfrom @PriceGraph </b>"
                )
            await app.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
            if combined_image:
                image_bytes = BytesIO()
                combined_image.save(image_bytes, format='JPEG')
                image_bytes.seek(0)
                await app.send_photo(message.chat.id, photo=image_bytes, caption=caption)
            else:
                await app.send_message(message.chat.id, caption)

            if str(message.chat.id) in DealerID:
                dealer_caption = (
                    f"<b>{inputvalue.replace(extracted_link, f'<a href={affiliate_url}> Buy Now</a>')}</b>"
                    + promo_footer()
                )
                notify = should_notify(Target_Channel_id)
                if forward == True:
                    if combined_image:
                        image_bytes = BytesIO()
                        combined_image.save(image_bytes, format='JPEG')
                        image_bytes.seek(0)
                        await app.send_photo(chat_id=Target_Channel_id, photo=image_bytes,
                                             caption=dealer_caption, reply_markup=promo_markup(), disable_notification=not notify)
                    else:
                        await app.send_message(chat_id=Target_Channel_id, text=dealer_caption,
                                               reply_markup=promo_markup(), disable_notification=not notify)
                else:
                    if combined_image:
                        image_bytes = BytesIO()
                        combined_image.save(image_bytes, format='JPEG')
                        image_bytes.seek(0)
                        await app.send_photo(message.chat.id, photo=image_bytes, caption=dealer_caption,
                                             reply_markup=InlineKeyboardMarkup(
                                                 [[InlineKeyboardButton("Send to Channel", callback_data='Send')]]))
                    else:
                        await app.send_message(message.chat.id, dealer_caption,
                                               reply_markup=InlineKeyboardMarkup(
                                                   [[InlineKeyboardButton("Send to Channel", callback_data='Send')]]))

            # print('success')
    except Exception as e:
        print(e)
        user_info = f"User ID: {message.from_user.id}\nUsername: @{message.from_user.username}\nUser Input: {message.text}"
        error_message = f"Error: {str(e)}\n\nUser Info:\n{user_info}"
        contact_admin_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Contact Admin", url="https://t.me/imovies_contact_bot", )]])
        b = await app.send_message(admin_chat_id, error_message)
        user_error_message = f"Oops! Something went Wrong.\n👉Input Only Amazon Product Link..\n\n👉Don't send Post with Multiple Links..\nTry Again.Reported to the admin."
        b = await app.send_message(message.chat.id, user_error_message, reply_markup=contact_admin_button)
        await asyncio.sleep(10)
        await b.delete()
    await a.delete()
    await message.delete()


# Admin: broadcast, status, stats - private only.
@app.on_message(filters.private & filters.incoming & filters.command("broadcast"))
async def broadcast_cmd(app, message):
    await handle_broadcast_command(app, message)


@app.on_message(filters.private & filters.incoming & filters.command("status"))
async def status_cmd(app, message):
    await handle_status_command(app, message)


@app.on_message(filters.private & filters.incoming & filters.command("stats"))
async def stats_cmd(app, message):
    await handle_stats_command(app, message)


################promo on off#################################################################
OWNER_IDS = {
    int(value.strip())
    for value in (
        os.getenv("OWNER_CHAT_ID", "") + "," + os.getenv("OWNER_CHAT_IDS", "")
    ).split(",")
    if value.strip().lstrip("-").isdigit()
}
promo_admin_ids = {5886397642} | OWNER_IDS


def is_promo_admin(message):
    return message.from_user is not None and message.from_user.id in promo_admin_ids

promo_on_kb = InlineKeyboardMarkup([[InlineKeyboardButton("ON ✅", callback_data='promo on')]])
promo_off_kb = InlineKeyboardMarkup([[InlineKeyboardButton("OFF 🚫", callback_data='promo off')]])

@app.on_message(filters.command('promo') & filters.incoming)
async def promo_cmd(app, message):
    global promo_enabled
    if not is_promo_admin(message):
        await message.reply_text("Not allowed")
        return
    if len(message.command) > 1:
        option = message.command[1].lower()
        if option == "on":
            promo_enabled = True
        elif option == "off":
            promo_enabled = False
        else:
            await message.reply_text("Usage: /promo [on|off]")
            return
    await message.reply_text(
        f"Promo currently: {'ON ✅' if promo_enabled else 'OFF 🚫'}\nToggle below:",
        reply_markup=promo_on_kb if promo_enabled else promo_off_kb
    )

# Silent button command like /forward
@app.on_message(filters.command('silent') & filters.incoming)
async def silent_cmd(app, message):
    global silent_interval
    if not is_promo_admin(message):
        await message.reply_text("Not allowed")
        return
    if len(message.command) > 1:
        try:
            interval = int(message.command[1])
        except ValueError:
            interval = 0
        if interval not in {2, 3, 5, 10}:
            await message.reply_text("Usage: /silent [2|3|5|10]")
            return
        silent_interval = interval
        await message.reply_text(
            f"Silent: notify every {silent_interval} posts."
        )
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("2 posts", callback_data='silent 2')],
        [InlineKeyboardButton("3 posts (default)", callback_data='silent 3')],
        [InlineKeyboardButton("5 posts", callback_data='silent 5')],
        [InlineKeyboardButton("10 posts", callback_data='silent 10')],
    ])
    await message.reply_text(f"Silent interval: notify every {silent_interval} posts. Choose:", reply_markup=kb)


# Run the bot

@bot.before_serving
async def before_serving():
    await app.start()
    # Resolve peers with retries so session independence is maintained (like diskfun/diskfun.py)
    targets = (
        (AUTH_CHANNEL, "auth"),
        (Target_Channel_id, "target"),
    ) + tuple((d, f"dealer_{d}") for d in DealerID if str(d).isdigit() or str(d).lstrip('-').isdigit())
    for chat_id, name in targets:
        for attempt in range(5):
            try:
                await app.get_chat(int(chat_id))
                logger.info("Resolved %s peer: %s", name, chat_id)
                break
            except Exception as exc:
                logger.warning("%s peer resolve %s/5 failed (%s): %s", name, attempt + 1, chat_id, exc)
                await asyncio.sleep(1 + attempt)
        else:
            logger.warning("%s peer %s still unresolved. Will self-heal on live update.", name, chat_id)
    await init_multibot(app)
    await app.send_message(chat_id=5886397642, text='Bot starting')


@bot.after_serving
async def after_serving():
    await app.send_message(chat_id= 5886397642, text='Bot Stopping')
    await app.stop()


# if __name__ == '__main__':

# bot.run(port=8000)
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(bot.run_task(host='0.0.0.0', port=8000))
    loop.run_forever()




