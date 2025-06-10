from telebot import types, TeleBot
from datetime import datetime, timedelta
import json
import threading
import time
import uuid
import logging
import sys
import traceback
from app6 import server


# إعداد التسجيل (Logging) لمراقبة الأخطاء
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# إعدادات البوت
API_TOKEN = '7096390944:AAF_hgRgDRSGnAbUAfcXNUlJsPsXF7aThtc'
CHANNEL_ID = -1002869371757
CHANNEL_INVITE_LINK = 'https://t.me/+j-j0Ypc66OYxNzVh'
OWNER_CHAT_ID = 768127968
SUPPORT_USERNAME = '@Mkk900'
SELLER_USERNAME = '@Mkk900'

bot = TeleBot(API_TOKEN)

# تخزين البيانات
DATA_FILE = 'bot_data.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("ملف البيانات غير موجود، يتم إنشاء ملف جديد")
        return {
            'users': {},
            'subscriptions': {},
            'codes': {},
            'used_codes': []
        }
    except json.JSONDecodeError as e:
        logger.error(f"خطأ في تحميل ملف البيانات: {e}")
        return {
            'users': {},
            'subscriptions': {},
            'codes': {},
            'used_codes': []
        }

def save_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4, default=str)
    except Exception as e:
        logger.error(f"خطأ في حفظ البيانات: {e}")

data = load_data()
users = data.get('users', {})
subscriptions = data.get('subscriptions', {})
codes = data.get('codes', {})
used_codes = data.get('used_codes', [])

# دوال مساعدة
def save_user(chat_id, username):
    users[str(chat_id)] = {
        'username': username or 'غير متوفر',
        'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    data['users'] = users
    save_data(data)

def save_subscription(chat_id, duration_days):
    expiry_date = datetime.now() + timedelta(days=duration_days)
    subscriptions[str(chat_id)] = {
        'expiry_date': expiry_date.strftime('%Y-%m-%d %H:%M:%S'),
        'active': True
    }
    data['subscriptions'] = subscriptions
    save_data(data)
    send_channel_invite(chat_id)

def send_channel_invite(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn_join = types.InlineKeyboardButton('الانضمام للقناة', url=CHANNEL_INVITE_LINK)
    markup.add(btn_join)
    try:
        bot.send_message(chat_id, "🎉 تم تفعيل اشتراكك! انضم إلى القناة الآن:", reply_markup=markup)
    except Exception as e:
        logger.error(f"فشل إرسال دعوة القناة إلى {chat_id}: {e}")

def send_notification(chat_id, message):
    try:
        bot.send_message(chat_id, message)
    except Exception as e:
        logger.error(f"فشل إرسال الإشعار إلى {chat_id}: {e}")

# أمر البدء
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        chat_id = message.chat.id
        username = message.from_user.username
        save_user(chat_id, username)

        markup = types.InlineKeyboardMarkup()
        btn_subscribe = types.InlineKeyboardButton('🛒 الاشتراك', callback_data='subscribe')
        btn_check = types.InlineKeyboardButton('📅 التحقق من الاشتراك', callback_data='check_subscription')
        btn_buy = types.InlineKeyboardButton('💳 شراء كود', url=f'https://t.me/{SELLER_USERNAME.lstrip("@")}')
        btn_support = types.InlineKeyboardButton('🛠 الدعم الفني', url=f'https://t.me/{SUPPORT_USERNAME.lstrip("@")}')
        markup.add(btn_subscribe, btn_check)
        markup.add(btn_buy, btn_support)

        welcome_message = (
            "👋 أهلًا بك في بوت الاشتراكات الخاص بكورس **الرياضيات**!\n\n"
            "📌 للوصول إلى محتوى القناة:\n"
            "1️⃣ اضغط على زر **شراء الأكواد**.\n"
            "2️⃣ تواصل مع **الأدمن** لشراء كود الاشتراك.\n"
            "3️⃣ بعد الحصول على الكود، استخدم زر **الاشتراك** لتفعيل اشتراكك.\n\n"
            "🎯 استعد لرحلة تعليمية مميزة ومفيدة!\n"
            "🚀 نتمنى لك تجربة ممتعة ومليئة بالنجاح."
        )
        bot.send_message(chat_id, welcome_message, reply_markup=markup)
    except Exception as e:
        logger.error(f"خطأ في معالجة أمر /start: {e}")

# باقي دوال معالجة الرسائل والاستعلامات (كما في الكود الأصلي)
# [يتم الاحتفاظ بدوال مثل subscribe_callback، process_code، check_subscription_callback، إلخ، مع إضافة معالجة الأخطاء]

# معالجة طلبات الانضمام
@bot.chat_join_request_handler(func=lambda join_request: True)
def handle_join_request(join_request):
    try:
        user_id = join_request.from_user.id
        chat_id = join_request.chat.id

        if str(user_id) in subscriptions and subscriptions[str(user_id)]['active']:
            expiry_date = datetime.strptime(subscriptions[str(user_id)]['expiry_date'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() <= expiry_date:
                bot.approve_chat_join_request(chat_id, user_id)
                bot.send_message(user_id, "🎉 تم قبول طلب انضمامك إلى القناة!")
            else:
                subscriptions[str(user_id)]['active'] = False
                data['subscriptions'] = subscriptions
                save_data(data)
                bot.send_message(user_id, "⏰ انتهى اشتراكك. يرجى التجديد للانضمام إلى القناة.")
        else:
            bot.send_message(user_id, "❌ تحتاج إلى اشتراك نشط للانضمام إلى القناة.")
    except Exception as e:
        logger.error(f"خطأ في معالجة طلب الانضمام: {e}")

# التحقق من الاشتراكات المنتهية وإرسال الإشعارات
def check_subscriptions():
    while True:
        try:
            now = datetime.now()
            for user_id in list(subscriptions.keys()):
                if subscriptions[user_id]['active']:
                    expiry_date = datetime.strptime(subscriptions[user_id]['expiry_date'], '%Y-%m-%d %H:%M:%S')
                    time_left = expiry_date - now
                    
                    if timedelta(days=0) < time_left <= timedelta(days=1):
                        send_notification(user_id, "⏰ اشتراكك سينتهي خلال أقل من 24 ساعة. جدد الآن!")
                    
                    if now > expiry_date:
                        subscriptions[user_id]['active'] = False
                        try:
                            bot.kick_chat_member(CHANNEL_ID, int(user_id))
                            bot.unban_chat_member(CHANNEL_ID, int(user_id))
                            send_notification(user_id, "❌ انتهى اشتراكك. جدد للانضمام إلى القناة مرة أخرى.")
                        except Exception as e:
                            logger.error(f"خطأ في طرد المستخدم {user_id}: {e}")
                        data['subscriptions'] = subscriptions
                        save_data(data)
            
            time.sleep(30)  # التحقق كل ساعة
        except Exception as e:
            logger.error(f"خطأ في التحقق من الاشتراكات: {e}")
            time.sleep(60)  # إعادة المحاولة بعد دقيقة في حالة الخطأ

# تشغيل البوت مع إعادة المحاولة عند الأخطاء
def run_bot():
    while True:
        try:
            logger.info("بدء تشغيل البوت...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"خطأ في تشغيل البوت: {e}")
            logger.error(traceback.format_exc())
            time.sleep(10)  # الانتظار 10 ثوانٍ قبل إعادة المحاولة
            logger.info("إعادة تشغيل البوت...")

if __name__ == "__main__":
    server()
    # بدء خيط الخلفية للتحقق من الاشتراكات
    threading.Thread(target=check_subscriptions, daemon=True).start()
    # تشغيل البوت
    run_bot()
