import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from flask import Flask
from threading import Thread

API_TOKEN = '7574811270:AAGwwen8Q5LHxdGVkMXQ8CgHsxhSf6auoAs'
ADMIN_ID = 216924786  # استبدل ID الادمن هنا

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@app.route('/')
def ping():
    return "PONG! HELLO FROM MTC"

# قوام لتأكيد أو إلغاء الإرسال
def confirm_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("تأكيد الإرسال", callback_data="confirm"),
               InlineKeyboardButton("إلغاء الإرسال", callback_data="cancel"))
    return markup

# قوام "تم الإرسال بنجاح"
def sent_success_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تم الإرسال بنجاح ✅", callback_data="none"))
    return markup

# قاموس لتخزين الرسائل المؤقتة
pending_messages = {}

# أمر البدء
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        welcome_text = "مرحبا بك في مؤسسة النجاح 📝\nأرسل رسالتك وسوف نقوم بالرد عليك في أقرب وقت."
        bot.send_message(message.chat.id, welcome_text)
    except Exception as e:
        print(f"Error in send_welcome: {e}")

# استقبال الرسائل من المستخدمين (مع التأكد من أن المرسل ليس الأدمن)
@bot.message_handler(func=lambda message: message.from_user.id != ADMIN_ID)
def handle_message(message):
    try:
        # حفظ الرسالة مؤقتًا
        pending_messages[message.chat.id] = message
        # عرض خيارات تأكيد أو إلغاء الإرسال
        bot.send_message(message.chat.id, "هل تريد تأكيد إرسال الرسالة للادمن؟", reply_markup=confirm_markup())
    except Exception as e:
        print(f"Error in handle_message: {e}")

# معالجة اختيارات المستخدم (تأكيد أو إلغاء)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        user_id = call.message.chat.id
        if call.data == "confirm":
            if user_id in pending_messages:
                bot.forward_message(ADMIN_ID, user_id, pending_messages[user_id].message_id)
                bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=sent_success_markup())
            else:
                bot.send_message(user_id, "لا توجد رسالة لإرسالها.")
        elif call.data == "cancel":
            bot.send_message(user_id, "تم إلغاء إرسال الرسالة.")
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id)

        # إزالة الرسالة من القائمة المؤقتة
        if user_id in pending_messages:
            del pending_messages[user_id]
    except Exception as e:
        print(f"Error in handle_callback: {e}")

# التعامل مع رد الادمن على الرسائل المحولة
@bot.message_handler(func=lambda message: message.reply_to_message and message.from_user.id == ADMIN_ID, content_types=['text', 'photo', 'video', 'document'])
def handle_admin_reply(message):
    try:
        original_message = message.reply_to_message
        original_user_id = original_message.forward_from.id if original_message.forward_from else None

        if original_user_id:
            bot.copy_message(original_user_id, message.chat.id, message.message_id)
        else:
            bot.send_message(message.chat.id, "لم أتمكن من العثور على المستخدم الأصلي.")
    except Exception as e:
        print(f"Error in handle_admin_reply: {e}")

def run():
    try:
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        print(f"Error in Flask server: {e}")

def server():
    t = Thread(target=run)
    t.start()

server()

# وضع polling في try-except لمنع توقف البوت في حال وجود خطأ غير متوقع
while True:
    try:
        bot.polling(none_stop=True, timeout=60)  # استخدم timeout لتجنب أي مشاكل في الاتصال
    except Exception as e:
        print(f"Error in bot polling: {e}")
                     
