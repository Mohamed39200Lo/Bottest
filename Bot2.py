from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from app import server
import requests
from flask import Flask
from threading import Thread
API_TOKEN = '7425541614:AAGhkWzA1uM6QWksUvlUC2slqLGOSSEJvbk'
bot = telebot.TeleBot(API_TOKEN)


app = Flask(__name__)

@app.route('/')
def ping():
    return "PONG !, HELLO FROM MTC"


chat_id = "-1002037612532"  

url = "https://www.dzrt.com/ar/our-products.html"
notified_products = set()
current_message_content = ""

# Initialize Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")

import os

def save_and_send_page_source():
    # Save the page source to a file
    file_path = "page_source.html"
    with open(file_path, 'w') as f:
        f.write(driver.page_source)
    
    # Check if the file exists and send it via the bot
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            bot.send_document(chat_id, file)
        
        # Optionally, remove the file after sending
        os.remove(file_path)



driver = webdriver.Chrome( options=chrome_options)

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
        print(f"Error getting pinned message: {e}")
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
                        print(f"No change in the message content: {e}")
                    else:
                        print(f"Error editing message: {e}")
                        pinned_message_id = None  
            if not pinned_message_id:
                sent_message = bot.send_message(chat_id, new_message_content, parse_mode='Markdown')
                bot.pin_chat_message(chat_id, sent_message.message_id)
            current_message_content = new_message_content

        except Exception as e:
            print(f"Unexpected error updating pinned message: {e}")

def check_availability():
    try:
        driver.get(url)
        # Wait until products are loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product-item"))
        )

        product_statuses = {}
        products = driver.find_elements(By.CLASS_NAME, 'product-item')

        for product in products:
            
            name = driver.execute_script("return arguments[0].textContent;", product.find_element(By.CSS_SELECTOR, 'a.product-item-link')).strip()
            
            link = product.find_element(By.CLASS_NAME, 'product-item-link').get_attribute('href')
            image_tag = product.find_element(By.CLASS_NAME, 'product-image-photo')
            image_url = image_tag.get_attribute('data-src') if image_tag else "https://assets.dzrt.com/media/wysiwyg/Home-New/dzrt-hand-product-can-ar.png"

            # Check availability
            availability = product.find_elements(By.CLASS_NAME, 'stock unavailable')
            is_available = len(availability) == 0

            product_statuses[name] = {'available': is_available, 'link': link, 'image_url': image_url}

            # Add debugging statement
            print(f"Checking product: {name} | Available: {is_available}")

            # Notify if the product is available and hasn't been notified
            if  is_available and name not in notified_products:
                
                markup = InlineKeyboardMarkup()
                markup.row_width = 2
                markup.add(
                    InlineKeyboardButton("عرض المنتج 🛍️", url=link),
                    InlineKeyboardButton("تسجيل الدخول", url="https://www.dzrt.com/ar/customer/account/login/referer/aHR0cHM6Ly93d3cuZHpydC5jb20vYXIvc3BpY3ktY291cnNlLmh0bWw/")
                )
                markup.add(
                    InlineKeyboardButton("سلة المنتجات 🗑️", url="https://www.dzrt.com/ar/checkout/cart/")
                )

                caption = f"تم توافر المنتج {name}\n\n انظر الرسالة المثبتة لمعرفة جميع المنتجات المتوفرة حالياً 📌"
                bot.send_photo(chat_id, image_url, caption=caption, reply_markup=markup, parse_mode='Markdown')
                notified_products.add(name)  # Mark as notified

            # If the product becomes unavailable, remove from notifications
            elif not is_available and name in notified_products:
                notified_products.remove(name)

        update_pinned_message(product_statuses)
        save_and_send_page_source()

    except requests.exceptions.RequestException as e:
        print(f"Error during HTTP request: {e}", file=stderr)

    except Exception as e:
        save_and_send_page_source()
        print(f"Unexpected error during availability check: {e}")

def run():
    app.run(host='0.0.0.0', port=8080)

def server():
    t = Thread(target=run)
    t.start()

        
if __name__ == "__main__":
    server()
    while True:
        check_availability()
        time.sleep(60)

# Close driver after script ends
driver.quit()
