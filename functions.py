import asyncio
import logging
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
from urllib.parse import urlparse, urlunparse, parse_qs
import re
import os

from amazon_paapi import get_asin
from amazon_creatorsapi import AmazonCreatorsApi, Country
from bs4 import BeautifulSoup
from unshortenit import UnshortenIt
from pyrogram import Client, filters, enums
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PAAPI_CREDENTIAL_ID = os.getenv('PAAPI_CREDENTIAL_ID')
PAAPI_CREDENTIAL_SECRET = os.getenv('PAAPI_CREDENTIAL_SECRET')
PAAPI_TAG = os.getenv('PAAPI_TAG', 'pgraph-21')
AFFILIATE_TAG_IN = os.getenv('AFFILIATE_TAG_IN', 'wishlink_923495-21')
AFFILIATE_TAG_GLOBAL = os.getenv('AFFILIATE_TAG_GLOBAL', 'lootcom-20')

amazon_in = AmazonCreatorsApi(
    credential_id=PAAPI_CREDENTIAL_ID,
    credential_secret=PAAPI_CREDENTIAL_SECRET,
    version='3.2',
    tag=PAAPI_TAG,
    country=Country.IN,
)


def extract_link_from_text(text):
    url_pattern = r'https?://\S+'
    urls = re.findall(url_pattern, text)
    if len(urls) > 1:
        return None
    return urls[0] if urls else None


def unshorten_url(short_url):
    return UnshortenIt().unshorten(short_url)


def remove_amazon_affiliate_parameters(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    if 'ru' in query_params:
        query_params = {key: value for key, value in query_params.items() if key == 'ru'}
        parsed_url = urlparse(query_params['ru'][0])
        query_params = parse_qs(parsed_url.query)

    strip_params = ['tag', 'ref', 'linkCode', 'camp', 'creative', 'linkId', 'ref_', 'language', 'content-id', '_encoding']
    cleaned = {k: v for k, v in query_params.items() if k not in strip_params}
    return urlunparse(parsed_url._replace(query='&'.join([f'{k}={v[0]}' for k, v in cleaned.items()])))


def create_amazon_affiliate_url(normal_url, affiliate_tag):
    if "amazon" not in normal_url:
        return normal_url
    separator = '&' if '?' in normal_url else '?'
    return f"{normal_url}{separator}tag={affiliate_tag}"


def extract_country_code(url):
    # Handles multi-part TLDs like co.uk, co.jp, com.br
    match = re.search(r"amazon\.([\w.]+?)(?:/|\?|$)", url)
    return match.group(1).lower() if match else 'in'


def keepa_process(url):
    country_code = extract_country_code(url)

    product_code_match = re.search(r'/dp/([A-Za-z0-9]{10})', url)
    if not product_code_match:
        product_code_match = re.search(r'/product/([A-Za-z0-9]{10})', url)
    product_code = product_code_match.group(1) if product_code_match else None

    keepa_url = f'https://graph.keepa.com/pricehistory.png?asin={product_code}&domain={country_code}'
    amazon_url = f'https://www.amazon.{country_code}/dp/{product_code}'

    affiliate_tag = AFFILIATE_TAG_IN if country_code == 'in' else AFFILIATE_TAG_GLOBAL
    affiliate_url = create_amazon_affiliate_url(amazon_url, affiliate_tag)

    return keepa_url, amazon_url, affiliate_url


async def get_product_details(url):
    country_code = extract_country_code(url)
    if country_code == 'in':
        asin = get_asin(url)
        logger.debug(f"[PAAPI] get_items asin={asin} tag={PAAPI_TAG}")
        try:
            product = amazon_in.get_items(asin)[0]
        except Exception as e:
            logger.error(f"[PAAPI] get_items failed asin={asin}: {type(e).__name__}: {e}")
            raise
        name = product.item_info.title.display_value
        img_url = product.images.primary.large.url
        price = str(product.offers_v2.listings[0].price.money.amount) if product.offers_v2 else ' '
        return name, img_url, price
    else:
        return await _scrape_product_details(url)


async def _scrape_product_details(url):
    """Scrape title and image from non-IN Amazon pages.
    Price is intentionally omitted — amazon.com served from Indian IPs returns
    geo-converted INR prices that are misleading. User gets actual price via the link."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title_el = soup.find('span', {'id': 'productTitle'})
            image_el = soup.find('img', {'id': 'landingImage'})
            name = title_el.text.strip() if title_el else 'Amazon Product'
            img_url = image_el.get('src') if image_el else None
            return name, img_url, 'Check link for current price'
    except Exception:
        pass
    return 'Amazon Product', None, 'Check link for current price'


def add_banner(image, text):
    width, height = image.size
    banner_height = 50
    new_image = Image.new('RGB', (width, height + banner_height), color='white')
    new_image.paste(image, (0, banner_height))
    draw = ImageDraw.Draw(new_image)
    font = ImageFont.truetype("arial.ttf", 24)
    text_position = (10, 10)
    text_bbox = draw.textbbox(text_position, text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    draw.rectangle(
        [(text_position[0] - 5, text_position[1] - 5),
         (text_position[0] + text_width + 5, text_position[1] + text_height + 5)],
        fill="yellow"
    )
    draw.text(text_position, text, fill="blue", font=font)
    return new_image


async def merge_images(image_urls):
    images = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    for url in image_urls:
        if not url:
            continue
        img = None
        if url.startswith('https://'):
            source = 'KEEPA' if 'graph.keepa.com' in url else 'PRODUCT_IMG'
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.warning(f"[{source}] fetch failed status={response.status_code} url={url}")
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                if 'graph.keepa.com' in url:
                    w, h = img.size
                    img = img.crop((0, 0, w - 80, h))
                else:
                    w, h = img.size
                    img = img.resize((w // 2, h // 2))
        if img:
            images.append(img)

    if not images:
        return None

    if len(images) == 1:
        return images[0].convert('RGB')

    # Stack vertically (product image on top, price graph below)
    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)
    combined = Image.new('RGB', (max_width, total_height), color='white')
    y_offset = 0
    for img in images:
        x_offset = (max_width - img.width) // 2
        combined.paste(img, (x_offset, y_offset))
        y_offset += img.height

    draw = ImageDraw.Draw(combined)
    font = ImageFont.load_default()
    draw.text((combined.width - 210, combined.height - 60), '@Amazon_PriceHistory_Bot', fill="blue", font=font)
    return combined
