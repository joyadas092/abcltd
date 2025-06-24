import urllib
import asyncio
from PIL import Image ,ImageDraw,ImageFont
from io import BytesIO
import time
import requests
import json
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

from amazon_paapi import AmazonApi, get_asin
from bs4 import BeautifulSoup
import time
import requests as request
from urllib.parse import urlparse, parse_qs, urlunparse
import requests
import re
from unshortenit import UnshortenIt
# from selenium.webdriver.common.by import By
from unshortenit import UnshortenIt
# from selenium.webdriver.common.action_chains import ActionChains
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.options import Options

from pyrogram import Client, filters, enums
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium import webdriver
user_data_dir = "C:\\Users\\shash\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 6"

# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
# # chrome_options.add_argument("--headless")
# # chrome_options.add_argument("--disable-dev-shm-usage")
# # chrome_options.add_argument("--no-sandbox")
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
# driver.maximize_window()


KEY='AKIAIB5643SVT3UOEEOQ'
SECRET='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'
TAG='pgraph-21'
COUNTRY='IN'


affiliate_id = "rohanpouri&affExtParam1=ENKR20240401A827654015&affExtParam2=ENKR20240401A827654015"
apitoken='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2M2U2MjEwNjYwOWU1YWY4ZTc4OTU2NTEiLCJlYXJua2FybyI6IjI1MjM2ODEiLCJpYXQiOjE3MTQzMzcxMDZ9.WOP7a-VJpEvg5p1sOpujkFJlcGjk50rq55ixeyHunK4'

amazon = AmazonApi(KEY, SECRET, TAG, COUNTRY)

def extract_link_from_text(text):
    # Regular expression pattern to match a URL
    url_pattern = r'https?://\S+'

    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    if len(urls)>1:
        return None

    return urls[0] if urls else None

def unshorten_url(short_url):
    unshortener = UnshortenIt()
    shorturi = unshortener.unshorten(short_url)
    # print(shorturi)
    return shorturi
    # response = requests.head(short_url, allow_redirects=True,timeout=2)
    #
    # return response.url

def remove_amazon_affiliate_parameters(url):
    parsed_url = urlparse(url)
    # print(parsed_url)
    query_params = parse_qs(parsed_url.query)
    # print('query_params: '+str(query_params))
    if 'ru' in query_params:
        query_params={key: value for key, value in query_params.items() if key == 'ru'}
        parsed_url = urlparse(query_params['ru'][0])
        query_params = parse_qs(parsed_url.query)


    # List of Amazon affiliate parameters to remove
    amazon_affiliate_params = ['tag', 'ref', 'linkCode', 'camp', 'creative','linkId','ref_','language','content-id','_encoding']

    # Remove the Amazon affiliate parameters from the query parameters
    cleaned_query_params = {key: value for key, value in query_params.items() if key not in amazon_affiliate_params}
    # Rebuild the URL with the cleaned query parameters
    cleaned_url = urlunparse(parsed_url._replace(query='&'.join([f'{key}={value[0]}' for key, value in cleaned_query_params.items()])))

    return cleaned_url

def create_amazon_affiliate_url(normal_url, affiliate_tag):
    if "amazon" not in normal_url:
        return "Not a valid Amazon Product link."

    if not affiliate_tag:
        return "Please provide a valid affiliate tag."

    # Check if the URL already has query parameters
    separator = '&' if '?' in normal_url else '?'

    # Append the affiliate tag to the URL
    affiliate_url = f"{normal_url}{separator}tag={affiliate_tag}"

    return affiliate_url

def keepa_process(url):
# Extract the country code using regular expressions
    country_code_match = re.search(r"amazon\.(\w+)/", url)
    country_code = country_code_match.group(1) if country_code_match else None
    # Extract the product code using regular expressions
    product_code_match = re.search(r"/product/([A-Za-z0-9]{10})", url)

    product_code_match2 = re.search(r'/dp/([A-Za-z0-9]{10})', url)
    product_code = product_code_match.group(1) if product_code_match else product_code_match2.group(1)

    # print("Product Code:", product_code)
    # print("Country Code:", country_code)

    keepa_url=f'https://graph.keepa.com/pricehistory.png?asin={product_code}&domain={country_code}'

    amazon_url=f'https://www.amazon.{country_code}/dp/{product_code}'
    affiliate_url=create_amazon_affiliate_url(amazon_url,affiliate_tag='pgraph-21' if country_code=='in'else 'highfivesto0c-20')

    return keepa_url,amazon_url,affiliate_url

# async def get_product_details(url):
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
#     }

#     async with aiohttp.ClientSession() as session:
#         retries = 1
#         for i in range(40):
#             # print(i)
#             if 'amazon' not in url:
#                 return None

#             async with session.get(url, headers=headers) as response:
#                 if response.status == 200:
#                     html = await response.text()
#                     soup = BeautifulSoup(html, 'html.parser')
#                     product_title = soup.find('span', {'id': 'productTitle'})
#                     product_image = soup.find('img', {'id': 'landingImage'})
#                     price_element = soup.find('span', {'class': 'a-offscreen'})
#                     unavailable_element = soup.find(lambda tag: tag.name == 'span' and
#                                                      tag.get('class') == ['a-size-medium a-color-success'] and
#                                                      tag.text.strip() == 'Currently unavailable.')

#                     if product_image:
#                         img_url = product_image.get('src')

#                     if product_title:
#                         amazon_product_name = product_title.text.strip()

#                         if unavailable_element:
#                             price_element = 'Out Of Stock'
#                         elif price_element:
#                             price_element = price_element.text.strip()
#                         else:
#                             price_element = 'Unable to get Price'
#                         # print(amazon_product_name,img_url,price_element)
#                         return amazon_product_name, img_url, price_element

#                 elif response.status == 503:
#                     if i==30:
#                         print("503 Error: Server busy, retrying...")
#                         break

#                 elif response.status == 404:
#                     if i==30    :
#                         print("Error 404:", response.status)
#                         break

#             await asyncio.sleep(1)  # Wait before retrying

#     return None
async def get_product_details(url):

    asin=get_asin(url)
    # print(asin)
    SearchProduct=amazon.get_items(asin)[0]
    amazon_product_name= SearchProduct.item_info.title.display_value
    img_url=SearchProduct.images.primary.large.url
    if SearchProduct.offers:
        price_element=str(SearchProduct.offers.listings[0].price.display_amount)
    else:
        price_element=' '
    return amazon_product_name, img_url, price_element

def add_banner(image, text):
    width, height = image.size
    banner_height = 50  # Height of the banner

    # Create a new image with extra space at the top for the banner
    new_image = Image.new('RGB', (width, height + banner_height), color='white')
    new_image.paste(image, (0, banner_height))

    # Add text to the banner with a yellow background
    draw = ImageDraw.Draw(new_image)
    font = ImageFont.truetype("arial.ttf", 24)  # Larger font size
    text_position = (10, 10)

    # Calculate text bounding box
    text_bbox = draw.textbbox(text_position, text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Draw yellow rectangle background
    draw.rectangle([(text_position[0] - 5, text_position[1] - 5),
                    (text_position[0] + text_width + 5, text_position[1] + text_height + 5)],
                   fill="yellow")

    # Draw text on top
    draw.text(text_position, text, fill="blue", font=font)

    return new_image


async def merge_images(image_urls):
    images = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    for url in image_urls:
        img=None
        # print(url)
        if 'https:/' in url :
            response = requests.get(url,headers=headers)
            # print('gg')
            if response.status_code==200:
                img = Image.open(BytesIO(response.content))
                if 'https://graph' in url:
                    width, height = img.size
                    new_width = width - 80  # Adjust the amount to be cropped from the right as needed
                    img = img.crop((0, 0, new_width, height))
                else:
                    width, height = img.size

                    # Define the desired width and height for the smaller image
                    new_width = width // 2  # Halving the width
                    new_height = height // 2  # Halving the height

                    # Resize the image
                    img = img.resize((new_width, new_height))

        if img:
            images.append(img)
    # print('image count:', len(images))
    if len(images)==2:
        # Determine the size of the combined image
        total_width = sum(img.width for img in images)
        max_height = max(img.height for img in images)

        # Create a new blank image with the combined size
        combined_image = Image.new('RGB', (total_width, max_height))

        # Paste each image into the combined image
        x_offset = 0
        for img in images:
            combined_image.paste(img, (x_offset, 0))
            x_offset += img.width
        if len(images) == 2:
            total_width = sum(img.width for img in images)
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images)
            combined_image = Image.new('RGB', (max_width, total_height), color='white')
            y_offset = 0
            for img in images:
                x_offset = (max_width - img.width) // 2
                combined_image.paste(img, (x_offset, y_offset))
                y_offset += img.height
            # combined_image.show()
            # return combined_image
        draw = ImageDraw.Draw(combined_image)
        font = ImageFont.load_default()  # You can use a custom font if needed

        text_position = (combined_image.width - 210, combined_image.height - 60)
        draw.text(text_position, '@Amazon_PriceHistory_Bot', fill="blue", font=font)
        # combined_image = add_banner(combined_image, "Search @price_history_loots and Join")

        return  combined_image
    # Display or save the combined image
    # combined_image.show()
    else:
       return  images[0].convert('RGB')



# *****************************************************************************************************
def flipkartAffUrl(url,FLipkartAffId):
    # Parse the URL
    parsed_url = urlparse(url)

    # Parse the query string
    query_params = parse_qs(parsed_url.query)

    # Remove the affiliate parameters
    query_params.pop('affid', None)
    query_params.pop('affExtParam1', None)
    query_params.pop('affExtParam2', None)

    # Reconstruct the query string without the affiliate parameters
    updated_query = urlencode(query_params, doseq=True)

    # Reconstruct the URL with the updated query string
    updated_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        updated_query,
        parsed_url.fragment
    ))
    pattern = r'pid=([a-zA-Z0-9]{16})'
    # Find the match in the URL
    match = re.search(pattern, updated_url)
    if match:
        # Get the matched PID value
        pid_value = match.group(1)
        # Trim everything after the PID value in the URL
        trimmed_url = url[:match.start()] + f"pid={pid_value}"
        # print(trimmed_url)

    return trimmed_url + '&affid=' + FLipkartAffId

def capture_element_screenshot(driver):
    # location = element.location
    screenshot = driver.get_screenshot_as_png()

    image = Image.open(BytesIO(screenshot))
    element_screenshot = image.crop((50, 225, image.width-50, image.height-180))
    image_bytes = BytesIO()
    element_screenshot.save(image_bytes, format='PNG')
    image_bytes.seek(0)

    return image_bytes


async def graphprocess(extracted_link):

    driver.get(extracted_link)  # Open the URL
    final_url = driver.current_url
    if 'pid=' not in final_url:
        return None

    Screenshot = driver.get_screenshot_as_png()
    # if 'amazon.in' in final_url:
    #     driver.find_element(By.XPATH,"//a[ @title='Text' and @href='javascript:void(0)']").click()
    #     time.sleep(2)
    #     affiliateUrl=driver.find_element(By.XPATH,"//*[@id='amzn-ss-text-shortlink-textarea']").text
    #     if affiliateUrl:
    #         print(affiliateUrl)
    #         print('success')
    #     else:
    #         print('notfound')
    # if 'flipkart' in final_url:
    #      # afftext=ekconvert(text)
    #     affiliateUrl=flipkartAffUrl(final_url,affiliate_id)
    # else:
    #     affiliateUrl=None

    Productimage = Image.open(BytesIO(Screenshot))
    image_bytes = BytesIO()
    Productimage.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    # Productimage.show()

    driver.get('https://pricehistoryapp.com/')
    driver.find_element(By.XPATH, "(//input[@placeholder='Enter name or paste the product link'])[1]").send_keys(
        final_url)
    driver.find_element(By.XPATH, "//button[@title='Search Price History']").click()
    wait = WebDriverWait(driver, 10)
    graphele = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='apexchartspriceHistory']")))

    driver.execute_script("arguments[0].scrollIntoView(); window.scrollBy(0, -150);", graphele)
    time.sleep(7)
    element_screenshot = capture_element_screenshot(driver)
    Graphimg = Image.open(element_screenshot)
    # Graphimg.show()

    images = [Productimage, Graphimg]

    if len(images) == 2:
        total_width = sum(img.width for img in images)
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)
        combined_image = Image.new('RGB', (max_width, total_height), color='white')
        y_offset = 0
        for img in images:
            x_offset = (max_width - img.width) // 2
            combined_image.paste(img, (x_offset, y_offset))
            y_offset += img.height
        # combined_image.show()
        return combined_image

async def ekconvert(text):
    url = "https://ekaro-api.affiliaters.in/api/converter/public"

    # inputtext = input('enter deal: ')
    payload = json.dumps({
        "deal": f"{text}",
        "convert_option": "convert_only"
    })
    headers = {
        'Authorization': f'Bearer {apitoken}',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # print(response.text)
    response_dict = json.loads(response.text)

    # Extract the "data" part from the dictionary
    data_value = response_dict.get('data')

    return(data_value)


def extract_links_from_text(text):
    # Regular expression pattern to match a URL
    url_pattern = r'https?://\S+'

    # Find all URLs in the text
    urls = re.findall(url_pattern, text)

    return urls
def extp(text):
    unshortened_urls = {}
    urls = extract_links_from_text(text)
    for url in urls:
        unshortened_urls[url] = unshorten_url(url)
    for original_url, unshortened_url in unshortened_urls.items():
        text = text.replace(original_url, unshortened_url)
    return text
