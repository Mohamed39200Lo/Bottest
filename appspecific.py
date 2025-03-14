import requests
from bs4 import BeautifulSoup
import time
import telebot
from sys import stderr
from threading import Thread
from flask import Flask
import cloudscraper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

chat_ids = ["-1002222132008","-1002443500870","-1002039608675"] 

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




def generate_products_message(products):
    message = "حالة المنتجات⏪ يتم تحديث هذه الرسالة باستمرار بوضع علامة ✅ امام المنتجات المتوفرة حالياً:\n\n" 
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


@bot.callback_query_handler(func=lambda call: call.data == "available_products")
def available_products_callback(call):
    print(3)
    if notified_products:
        
        available_products_list = "\n".join(f"✅ {product}" for product in notified_products)
        bot.answer_callback_query(call.id, f"المنتجات المتوفرة حالياً:\n{available_products_list}", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "لا توجد منتجات متوفرة حالياً", show_alert=True)

# قائمة المنتجات المستهدفة
target_products = ["ايسي رش", "سي سايد فروست"]

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

            # التحقق مما إذا كان المنتج من القائمة المستهدفة
            if name not in target_products:
                continue  # تجاهل المنتج إذا لم يكن من المنتجات المستهدفة

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
            if is_available and name not in notified_products:
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
            elif not is_available and name in notified_products:
                notified_products.remove(name)
                markup = InlineKeyboardMarkup()
                markup.row_width = 1
                markup.add(
                    InlineKeyboardButton("نفذ المنتج 🔴", url=link),
                )
                caption2 = f"المنتج نفذ 🔴{name}"

                for chat_id in chat_ids:
                    bot.send_photo(chat_id, image_url, caption=caption2, reply_markup=markup, parse_mode='Markdown')

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
import subprocess            
if __name__ == "__main__":
    mostaql_process = subprocess.Popen(["python", "mostaql.py"])
   
    # تشغيل Flask و Telegram polling في خيوط منفصلة
    flask_thread = Thread(target=run_flask)
    telegram_thread = Thread(target=run_telegram_bot)

    flask_thread.start()
    telegram_thread.start()

    while True:
        check_availability()
        time.sleep(5)
