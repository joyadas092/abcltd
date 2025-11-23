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
from  dotenv import load_dotenv
load_dotenv()

# api_id= '23194318'
# api_hash= '87b5e87cc338e36268e7d1992c9dce2d'
# # bot_token= '6840899571:AAEuwcRBjJq8ezOhBlamHX0du1frezpnjTA'
# bot_token='6832329506:AAE03cnH7yFSt4k5h3c6UNRXVOqEkb5T3ds'
#

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")


app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
admin_chat_id ='849188964'
AUTH_CHANNEL='-1002038980148'
DealerID=['5886397642','-1002060929372','-4247871412']
Target_Channel_id='-1002038980148'
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
        pass
    except Exception as e:
        logger.exception(e)
    else:
        if user.status != 'kicked':
            return True

@app.on_message(filters.command("start") & (filters.group | filters.private) & filters.incoming)
async def start(app, message):
    bot_info = await app.get_me()
    bot_username = bot_info.username
    if len(message.command) > 1:
        product_id = message.command[1]
        # print(product_id)
        await app.send_chat_action(message.chat.id , ChatAction.UPLOAD_PHOTO)

        url=f'https://www.amazon.in/dp/{product_id}'
        product_name, imageUrl, Price = await get_product_details(url)

        keepa_url, amazon_url, affiliate_url = keepa_process(url)

        seed = message.from_user.id
        combined_image = await merge_images([imageUrl, keepa_url])
        image_bytes = BytesIO()
        combined_image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)

        await app.send_photo(message.chat.id, photo=image_bytes,
                             caption=f"Product: {product_name}\n\nCurrent Price: <b>{Price}</b>\n\nBEST BUY LINK: <b>{affiliate_url}</b>\n\nfrom <b>@PriceGraph </b>",
                             reply_markup=Promo2)

    else:
        await app.send_chat_action(message.chat.id , ChatAction.TYPING)
        await app.send_message(
            message.chat.id,
            f"<b>Hey! I am {bot_username}.\n\n➡️ Just send me a valid Amazon.in product link. I will share the Price History Graph of the last 3 months😍😍\n\nBuy when the Price is Low📉\n\n<a href='https://t.me/Loots_Xpert/12'>👉 CLICK HERE TO SEE TUTORIAL 👈</a></b>",disable_web_page_preview=True
        )    # Check if the message is in a group
    
    # Check if the message is in a group

    # if message.chat.type== enums.ChatType.PRIVATE:
    #     await message.reply(
    #         "Hey! Just send me a valid Amazon product link. I will share you the Price History Graph of last 3 months😍😍\n\nBuy when the Price is Low📉")
miniapps=''' 
🚨🚨 Use Telegram Mini Apps and Free your Device Storage

Amazon 🛒 :   @amazon_india_mini_bot

Flipkart 🛍️:    @FLIPKART_Mini_bot

Ajio 👗:           @AJIO_Mini_bot

Myntra 👕 :    @MYNTRA_Mini_bot

Shopsy 🏠:    @SHOPSY_Mini_bot

Cleartrip ✈️ :  @CLEARTRIP_Mini_bot

Goibibo ✈️:   @GOIBIBO_Mini_bot


⚠️⚠️Join Individual Channel according to your Favourite Buying Website.😍😍

👉 PRICE HISTORY : @PriceGraph

👉 AMAZON : @amazon_loots_daily

👉 FLIPKART : @flipkart_loots_daily

👉 AJIO & MYNTRA : @Ajio_myntra_deals

👉 SHOPSY & MEESHO : @shopsymeesho

👉 Offers : @OffersXpert


Join All Add Folder 👇: 

https://t.me/addlist/FReIeSd3Hyg5NjJl
'''

Promo = InlineKeyboardMarkup(
     [[InlineKeyboardButton("PriceHistory Bot 🤖", url="https://t.me/Amazon_Pricehistory_Bot"),InlineKeyboardButton("🛍️ ProductsFinder Bot", url="https://t.me/ProductsFinder_Bot")],
      [InlineKeyboardButton("🎁 Main Channel", url="https://t.me/+HeHY-qoy3vsxYWU1"),InlineKeyboardButton("🔔 Join 2.0", url="https://t.me/+mUXCQYrUiKg0NDQ1")]
      ])
Promo2 = InlineKeyboardMarkup(
     [[InlineKeyboardButton("MAXIMUM DEALS 🛒", url="https://t.me/addlist/6R2xTLIL9JFkMWI1")],
      [InlineKeyboardButton("🔔 Main Channel ", url="https://t.me/+HeHY-qoy3vsxYWU1"),InlineKeyboardButton("Whatsapp Loots 💬", url="https://t.me/Loots_Xpert/33")]])

forward_off = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Turn Off", callback_data='forward off')]])
forward_on = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Turn ON", callback_data='forward on')]])
global forward
forward=True
@app.on_message(filters.command('forward') & filters.user(5886397642))
async def forwardtochannel(app,message):

    await message.reply(text='Forward Status',reply_markup=InlineKeyboardMarkup(
    [[InlineKeyboardButton("Turn ON", callback_data='forward on')],[InlineKeyboardButton("Turn Off", callback_data='forward off')]])
                        )

@app.on_callback_query()
async def callback_query(app,CallbackQuery):
    global forward
    if CallbackQuery.data=='forward off':
        await CallbackQuery.edit_message_text('Forward to Channel Status turned Off',reply_markup=forward_on)
        forward = False
    elif CallbackQuery.data=='forward on':
        await CallbackQuery.edit_message_text('Forward to Channel Status turned On',reply_markup=forward_off)
        forward = True
    elif CallbackQuery.data=='Send':
        a=CallbackQuery.message
        # with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        #     await a.download(file_name=temp_file.name)
        #     with open(temp_file.name, 'rb') as f:
        #         photo_bytes = BytesIO(f.read())
        await app.send_photo(chat_id=Target_Channel_id,caption_entities=a.caption_entities,caption=a.caption,photo=a.photo.file_id,reply_markup=Promo)
                             # photo=image_bytes,caption=f"<b>{inputvalue.replace(extracted_link, affiliate_url)}</b>",
                             # reply_markup=Promo)
        await CallbackQuery.answer(text='Sent to Channel✨', show_alert=True)

@app.on_message(filters.command("miniapps") & (filters.private) & filters.incoming)
async def start(app, message):
    await app.send_message(
            message.chat.id,
            f"<b>{miniapps}</b>"
        )




@app.on_message((filters.private & filters.incoming) | (filters.group & filters.incoming))
async def handle_text(app, message):
    bot_info = await app.get_me()
    bot_username = bot_info.username

    Join = InlineKeyboardMarkup(
         [[InlineKeyboardButton("Join Channel", url="https://t.me/+fzkzAoDc2k4xZjNl")]])

    if AUTH_CHANNEL and not await is_subscribed(app, message):
        await app.send_message(message.chat.id, '<b>Join Telegram Channel to Use this Bot 👇👇\n\nJOIN AND TRY AGAIN</b>',reply_markup=Join)
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

                inputvalue = pattern.sub(lambda x: hyperlinkurl.pop(0), inputvalue).replace('Regular Price', 'MRP')
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

                inputvalue = pattern.sub(lambda x: hyperlinkurl.pop(0), inputvalue).replace('Regular Price', 'MRP')
                if "😱 Deal Time" in inputvalue:
                    # Remove the part
                    inputvalue = inputvalue.split("😱 Deal Time")[0]


    except Exception as e:
         # Handle exceptions
        await app.send_message(message.chat.id, f"Something went wrong: {str(e)}")
    # a = await app.send_message(message.chat.id, "Just wait 5 Seconds⏳⏳....Bot is Working🤖>>>>")
    try:
        if 'LivegramBot'in inputvalue or 'You cannot forward someone' in inputvalue:
            await message.delete()
            return None
        extracted_link=extract_link_from_text(inputvalue)
        # print(extracted_link)
        a = await app.send_message(message.chat.id, "Just wait 5 Seconds⏳⏳....Bot is Working🤖>>>>")
        if not extracted_link:
            d = await app.send_message(message.chat.id, "Link not Found🫥🫥...")

            await a.delete()
            await d.delete()

            if message.chat.type == enums.ChatType.PRIVATE:
                await message.delete()
                e = await app.send_message(message.chat.id, "Searching Query in amazon.in...")

                search_result = amazon.search_items(keywords=inputvalue, item_count=8)

                for item in search_result.items:
                    response = requests.get(item.images.primary.large.url)
                    # print('gg')
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        image_bytes = BytesIO()
                        img.save(image_bytes, format='JPEG')
                        image_bytes.seek(0)

                    await app.send_photo(chat_id=message.chat.id, photo=image_bytes,
                                         caption=f"{item.item_info.title.display_value}\n\n Currrent Price : {item.offers.listings[0].price.amount}",
                                         reply_markup=InlineKeyboardMarkup(
                                             [[InlineKeyboardButton("BUY NOW", url=f'{item.detail_page_url}')],
                                              [InlineKeyboardButton("CLICK to See Price History 📉", url=f'https://t.me/{bot_username}?start={item.asin}')]
                                              ]))
                    await e.delete()

            return None

        # ##################################
        # if 'fkrt' in extracted_link or 'flipkart' in extracted_link:
        #     if str(message.chat.id) in DealerID and forward==True:
        #         if 'fkrt.co' in inputvalue:
        #             inputvalue = extp(inputvalue)
        #         affText= await ekconvert(inputvalue)
        #         combined_image= await graphprocess(extracted_link)
        #         image_bytes = BytesIO()
        #         combined_image.save(image_bytes, format='JPEG')
        #         image_bytes.seek(0)

        #         # await app.send_photo(message.chat.id, photo=image_bytes, caption=inputvalue.replace(extracted_link,
        #         #                                                                                     affiliateUrl) if affiliateUrl else inputvalue,
        #         #                     reply_markup=Promo)
        #         await app.send_photo(message.chat.id, photo=image_bytes, caption= affText,
        #                              reply_markup=Promo)
        #         if str(message.chat.id) in DealerID:
        #             await app.send_photo(chat_id=Target_Channel_id, photo=image_bytes,
        #                                  caption=f'{affText}</b>',
        #                                  reply_markup=Promo)
        #     else:
        #         e=await app.send_message(message.chat.id,"Flipkart Price History can be used only by my Admin🥺")
        #         await asyncio.sleep(5)
        #         await e.delete()
        #         await a.delete()
        #         await message.delete()
        #         return None

        # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


        # print(extracted_link)

        clean_url = remove_amazon_affiliate_parameters(unshorten_url(extracted_link))
        # print('clean url: '+clean_url)
        if 'amazon' in clean_url:

            product_name, imageUrl,Price = await get_product_details(clean_url)

            keepa_url, amazon_url, affiliate_url = keepa_process(clean_url)

            seed = message.from_user.id
            combined_image = await merge_images([imageUrl,keepa_url])
            image_bytes = BytesIO()
            combined_image.save(image_bytes, format='JPEG')
            image_bytes.seek(0)
            await app.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
            await app.send_photo(message.chat.id, photo=image_bytes, caption=f"Product: {product_name}\n\nCurrent Price: <b>{Price}</b>\n\n<b>You may get a CASHBACK!! Check Your Coupon Page Here👇👇 : \n\n🔗 https://amzn.to/3WMJyqy \n\nYour Product Link 👇👇:\n\n🔗{affiliate_url}\n\nfrom @PriceGraph </b>",reply_markup=Promo2)
            # print(message.chat.id)
            if str(message.chat.id) in  DealerID:
                # print(forward)
                if forward == True:
                    await app.send_photo(chat_id=Target_Channel_id, photo=image_bytes,
                                         caption=f"<b>{inputvalue.replace(extracted_link, f'<a href={affiliate_url}> Buy Now</a>')}</b>"+ "\n\n<b><a href ='https://t.me/addlist/zzZb8Deuzy9kZjQ1'>🛍️Click To Join for More Loots 👈</a></b>",
                                         reply_markup=Promo,disable_notification=True)
                else:
                    await app.send_photo(message.chat.id, photo=image_bytes,
                                         caption=f"<b>{inputvalue.replace(extracted_link, f'<a href={affiliate_url}> Buy Now</a>')}</b>"+"\n\n<b><a href ='https://t.me/addlist/zzZb8Deuzy9kZjQ1'>🛍️Click To Join for More Loots 👈</a></b>",
                                         reply_markup=InlineKeyboardMarkup(
                                             [[InlineKeyboardButton("Send to Channel", callback_data='Send')]]))


            # print('success')
    except Exception as e:
        print(e)
        user_info = f"User ID: {message.from_user.id}\nUsername: @{message.from_user.username}\nUser Input: {message.text}"
        error_message = f"Error: {str(e)}\n\nUser Info:\n{user_info}"
        contact_admin_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Contact Admin", url="https://t.me/imovies_contact_bot",)]])
        b = await app.send_message(admin_chat_id, error_message)
        user_error_message = f"Oops! Something went Wrong.\n👉Input Only Amazon Product Link..\n\n👉Don't send Post with Multiple Links..\nTry Again.Reported to the admin."
        b= await app.send_message(message.chat.id, user_error_message,reply_markup=contact_admin_button)
        await asyncio.sleep(10)
        await b.delete()
    await a.delete()
    await message.delete()
# Run the bot

@bot.before_serving
async def before_serving():

    await app.start()
    # await app.send_message(chat_id=Target_Channel_id,
    #                      text='<b>@AMAZON_PRICEHISTORY_BOT RESTARTED</b>',
    #                      )


@bot.after_serving
async def after_serving():

    # await app.send_message(chat_id=Target_Channel_id,
    #                      text='<b>@AMAZON_PRICEHISTORY_BOT WILL BE RESTARTED SHORTLY</b>',
    #                      )
    await app.stop()


# if __name__ == '__main__':

    # bot.run(port=8000)
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(bot.run_task(host='0.0.0.0', port=8000))
    loop.run_forever()



