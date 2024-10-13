import requests
from bs4 import BeautifulSoup
import time
import telebot
from sys import stderr
from threading import Thread
from flask import Flask
import cloudscraper
import tweepy  # إضافة مكتبة tweepy
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

chat_ids = ["-1002222132008","-1002443500870"] 

API_TOKEN = '5785640650:AAE7X0gMz5bfwfT6fuOJtEG10_5BjC4iBmE'
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

@app.route('/')
def ping():
    return "PONG !, HELLO FROM MTC"

chat_id = "-1002443500870"  
url = "https://www.dzrt.com/ar-sa/products"
notified_products = set()
current_message_content = ""

#🔴✅🔴

bearer_token = "AAAAAAAAAAAAAAAAAAAAABp4uQEAAAAAShyJO4ir5Qf9VXC5N3x%2FyVX6788%3DxBrKNxPsaWvkbwqCThV4HnRzIrv8719uNnPivxsGGtYjo9SxzO"
consumer_key = "NkHWqlGeh4pmgdlvYQoN43nrS"
consumer_secret = "UxDCRqydIdtWtT2rP1MYBeKRaQpRQAnf9uw9H4seQbJlRIoBx6"
access_token = "1709591850984652800-Hj6kpxAbYwllav2GxpdPkhdjkVLqUs"
access_token_secret = "OEki2DJLhKFXnAYP4gaUGcMKgItgJyooVm9uxlMrG3Hd5"

# إعداد تويتر API v2 باستخدام tweepy.Client
client = tweepy.Client(bearer_token=bearer_token, consumer_key=consumer_key, consumer_secret=consumer_secret,
                       access_token=access_token, access_token_secret=access_token_secret)

# وظيفة لإرسال تغريدة عند توفر "ايسي رش" أو "سي سايد فروست"
def send_tweet_about_availability(product_name, product_link):
    tweet_text = (f" توفر المنتج {product_name}! 🛍️\n"
                  f"رابط المنتج: {product_link}\n\n"
                  "انضم لقناة التليجرام للحصول على تنبيهات فورية لجميع المنتجات: "
                  "https://t.me/dzrt_bot_notifocation\n\n #DZRT")
    try:
        client.create_tweet(text=tweet_text)
        print(f"تم إرسال التغريدة: {tweet_text}")
    except Exception as e:
        print(f"حدث خطأ أثناء إرسال التغريدة: {e}")
        
        
#✅🔴✅
@bot.callback_query_handler(func=lambda call: call.data == "available_products")
def available_products_callback(call):
    print(3)
    if notified_products:
        
        available_products_list = "\n".join(f"✅ {product}" for product in notified_products)
        bot.answer_callback_query(call.id, f"المنتجات المتوفرة حالياً:\n{available_products_list}", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "لا توجد منتجات متوفرة حالياً", show_alert=True)

def check_availability():
    try:
        scraper = cloudscraper.create_scraper()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        response = scraper.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        products = soup.find_all('div', class_='relative bg-white px-2.5 pb-3 pt-6')

        product_statuses = {}

        for product in products:
            name_tag = product.find('span', class_='text-3.5 font-bold leading-5 text-custom-black-900')
            if name_tag:
                name = name_tag.get_text(strip=True)

            link_tag = product.find('a')
            if link_tag and 'href' in link_tag.attrs:
                link = "https://www.dzrt.com" + link_tag['href']
            else:
                print("No link found")
            status_tag = product.find('span', class_='absolute right-0 top-0 px-1.5 font-semibold uppercase text-white shadow-xs bg-custom-orange-700')
            is_available = status_tag is None

            # استخراج الصورة
            image_tag = product.find('img')
            if image_tag and 'src' in image_tag.attrs:
                image_url = "https://www.dzrt.com" + image_tag['src']
            else:
                image_url = "https://assets.dzrt.com/media/wysiwyg/Home-New/dzrt-hand-product-can-ar.png"

            product_statuses[name] = {'available': is_available, 'link': link, 'image_url': image_url}

            # إرسال إشعار إذا كانت السلعة متوفرة
            if   is_available and name not in notified_products:
                time.sleep(1)
                markup = InlineKeyboardMarkup()
                markup.row_width = 2
                markup.add(
                    InlineKeyboardButton("عرض المنتج 🛍️", url=link),
                    InlineKeyboardButton("تسجيل الدخول", url="https://www.dzrt.com/ar-sa/login")
                )
                markup.add(
                    InlineKeyboardButton("سلة المنتجات🛒", url="https://www.dzrt.com/ar-sa/cart"),
                    InlineKeyboardButton("صفحة الدفع 💳", url="https://www.dzrt.com/ar-sa/cart")                    
                
                )
                markup.add(
                    InlineKeyboardButton("المنتجات المتوفرة حالياً✅", callback_data="available_products"),
                                        
                
                )
                
                caption = f"تم توافر المنتج {name}"
                for chat_id in chat_ids:
                    bot.send_photo(chat_id, image_url, caption=caption, reply_markup=markup, parse_mode='Markdown')
                notified_products.add(name)
                if "ايسي رش" in name or "سي سايد فروست" in name:
                    send_tweet_about_availability(name, link)
            elif not is_available and name in notified_products:
                notified_products.remove(name)
                markup = InlineKeyboardMarkup()
                markup.row_width = 1
                markup.add(
                    InlineKeyboardButton("نفذ المنتج 🔴",url=link),
                    
                )
                caption2 = f"المنتج نفذ 🔴{name}"
                
                for chat_id in chat_ids:
                    bot.send_photo(chat_id, image_url, caption=caption2, reply_markup=markup, parse_mode='Markdown')
              

        #update_pinned_message(product_statuses)

    except requests.exceptions.RequestException as e:
        print(f"Error during HTTP request: {e}", file=stderr)
    except Exception as e:
        print(f"Unexpected error during availability check: {e}", file=stderr)



def run():
    app.run(host='0.0.0.0', port=8080)

def server():
    t = Thread(target=run)
    t.start()
def run_flask():
    app.run(host='0.0.0.0', port=8080)

def run_telegram_bot():
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)  # timeout لتجنب التعليق الطويل
        except Exception as e:
            print(f"Error in bot polling: {e}", file=stderr)
            time.sleep(5)  # تأخير قليل قبل المحاولة مرة أخرى
if __name__ == "__main__":
    # تشغيل Flask و Telegram polling في خيوط منفصلة
    flask_thread = Thread(target=run_flask)
    telegram_thread = Thread(target=run_telegram_bot)

    flask_thread.start()
    telegram_thread.start()

    while True:
        check_availability()
        time.sleep(5)

