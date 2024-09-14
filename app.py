import requests
from bs4 import BeautifulSoup
import time
import telebot

#from app import server
from sys import stderr
from threading import Thread
from flask import Flask

import cloudscraper
from bs4 import BeautifulSoup

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
#from app import server
import requests
#from flask import Flask, request

API_TOKEN = '7425541614:AAGhkWzA1uM6QWksUvlUC2slqLGOSSEJvbk'
bot = telebot.TeleBot(API_TOKEN)


app = Flask(__name__)

@app.route('/')
def ping():
    return "PONG !, HELLO FROM MTC"
    



chat_id = "-1002039608675"  

url = "https://www.dzrt.com/ar/our-products.html"
notified_products = set()
current_message_content = ""

def generate_products_message(products):
    message = " حالة المنتجات⏪ يتم تحديث هذه الرسالة باستمرار بوضع علامة ✅ امام المنتجات المتوفرة حالياً:\n\n" 
    for product, details in products.items():
        status = "✅" if details['available'] else "❌"
        link = details['link']
        message += f"{status} {product} -⬅️ [اطلب الآن]({link})\n"
    return message

def get_pinned_message_id():
    try:
        chat = bot.get_chat(chat_id)
        if chat.pinned_message:
            return chat.pinned_message.message_id
        else:
            return None
    except Exception as e:
        print(f"Error getting pinned message: {e}", file=stderr)
        return None

def update_pinned_message(products):
    global current_message_content
    new_message_content = generate_products_message(products)

    if new_message_content != current_message_content:
        try:
            pinned_message_id = get_pinned_message_id()
            if pinned_message_id:
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=pinned_message_id, text=new_message_content, parse_mode='Markdown')
                except telebot.apihelper.ApiTelegramException as e:
                    if "message is not modified" in str(e):
                        print(f"No change in the message content: {e}", file=stderr)
                    else:
                        print(f"Error editing message: {e}", file=stderr)
                        pinned_message_id = None  
            if not pinned_message_id:
                sent_message = bot.send_message(chat_id, new_message_content, parse_mode='Markdown')
                bot.pin_chat_message(chat_id, sent_message.message_id)
            current_message_content = new_message_content

        except Exception as e:
            print(f"Unexpected error updating pinned message: {e}", file=stderr)

def check_availability():
    try:
        # استخدام cloudscraper بدلاً من requests
        scraper = cloudscraper.create_scraper()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        response = scraper.get(url, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        soup = BeautifulSoup(response.content, 'html.parser')

        products = soup.find_all('li', class_='product-item')

        product_statuses = {}

        for product in products:
            name = product.find('a', class_='product-item-link').text.strip()
            link = product.find('a', class_='product-item-link')['href']
            image_tag = product.find('img', class_='product-image-photo')
            image_url = image_tag['data-src'] if image_tag and 'data-src' in image_tag.attrs else "https://assets.dzrt.com/media/wysiwyg/Home-New/dzrt-hand-product-can-ar.png"

            availability = product.find('div', class_='stock unavailable')

            is_available = availability is None
            product_statuses[name] = {'available': is_available, 'link': link, 'image_url': image_url}

            if  is_available and name not in notified_products:
                print(6)
                markup = InlineKeyboardMarkup()
                markup.row_width = 2
                markup.add(
                    InlineKeyboardButton("عرض المنتج 🛍️", url=link),
                    InlineKeyboardButton("تسجيل الدخول", url="https://www.dzrt.com/ar/customer/account/login/referer/aHR0cHM6Ly93d3cuZHpydC5jb20vYXIvc3BpY3kttemVzdC5odG1s/")
                )
                markup.add(
                    InlineKeyboardButton("سلة المنتجات 🗑️", url="https://www.dzrt.com/ar/checkout/cart/")
                )

                caption = f"تم توافر المنتج {name}\n\nانظر الرسالة المثبتة لمعرفة جميع المنتجات المتوفرة حالياً 📌"
                bot.send_photo(chat_id, image_url, caption=caption, reply_markup=markup, parse_mode='Markdown')
                notified_products.add(name)
            elif not is_available and name in notified_products:
                markup = InlineKeyboardMarkup()
                markup.row_width = 2
                markup.add(
                    InlineKeyboardButton("عرض المنتج 🛍️", url=link),
                    InlineKeyboardButton("تسجيل الدخول", url="https://www.dzrt.com/ar/customer/account/login/referer/aHR0cHM6Ly93d3cuZHpydC5jb20vYXIvc3BpY3k-temVzdC5odG1s/")
                )
                notification_message = f" المنتج {name} لم يعد متوفرًا!  ❌"
                bot.send_photo(chat_id, image_url, caption=notification_message,reply_markup=markup)
                                
                notified_products.remove(name)

        update_pinned_message(product_statuses)

    except requests.exceptions.RequestException as e:
        print(f"Error during HTTP request: {e}", file=stderr)
    except Exception as e:
        print(f"Unexpected error during availability check: {e}")


def run():
    app.run(host='0.0.0.0', port=8080)

def server():
    t = Thread(target=run)
    t.start()


# بدء التنفيذ
if __name__ == "__main__":
    server()
    while True:
        check_availability()
        print(5)
        time.sleep(20)
