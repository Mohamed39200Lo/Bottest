import telebot
from telebot import types
from datetime import datetime, timedelta
import json
import threading
import time
import uuid
import logging
import sys
import os
from app import server
# إعدادات التسجيل (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),  # تسجيل الأخطاء في ملف
        logging.StreamHandler(sys.stdout)  # طباعة الأخطاء في وحدة التحكم
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


bot = telebot.TeleBot(API_TOKEN)

# تخزين البيانات
DATA_FILE = 'bot_data.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("ملف البيانات غير موجود، يتم إنشاء ملف جديد.")
        return {
            'users': {},
            'subscriptions': {},
            'codes': {},
            'used_codes': []
        }
    except json.JSONDecodeError as e:
        logger.error(f"خطأ في تحليل ملف JSON: {e}")
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
    try:
        users[str(chat_id)] = {
            'username': username or 'غير متوفر',
            'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        data['users'] = users
        save_data(data)
    except Exception as e:
        logger.error(f"خطأ في حفظ المستخدم {chat_id}: {e}")

def save_subscription(chat_id, duration_days):
    try:
        expiry_date = datetime.now() + timedelta(days=duration_days)
        subscriptions[str(chat_id)] = {
            'expiry_date': expiry_date.strftime('%Y-%m-%d %H:%M:%S'),
            'active': True
        }
        data['subscriptions'] = subscriptions
        save_data(data)
        send_channel_invite(chat_id)
    except Exception as e:
        logger.error(f"خطأ في حفظ الاشتراك للمستخدم {chat_id}: {e}")

def send_channel_invite(chat_id):
    try:
        markup = types.InlineKeyboardMarkup()
        btn_join = types.InlineKeyboardButton('الانضمام للقناة', url=CHANNEL_INVITE_LINK)
        markup.add(btn_join)
        bot.send_message(chat_id, "🎉 تم تفعيل اشتراكك! انضم إلى القناة الآن:", reply_markup=markup)
    except Exception as e:
        logger.error(f"خطأ في إرسال دعوة القناة إلى {chat_id}: {e}")

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

# معالجة زر الاشتراك
@bot.callback_query_handler(func=lambda call: call.data == 'subscribe')
def subscribe_callback(call):
    try:
        chat_id = call.message.chat.id
        msg = bot.send_message(chat_id, "🔑 أدخل كود الاشتراك:")
        bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        logger.error(f"خطأ في معالجة زر الاشتراك: {e}")

def process_code(message):
    try:
        chat_id = message.chat.id
        code = message.text.strip()

        if code in used_codes:
            bot.send_message(chat_id, "❌ هذا الكود مستخدم بالفعل.")
        elif code in codes:
            duration_days = codes[code]['duration']
            save_subscription(chat_id, duration_days)
            used_codes.append(code)
            data['used_codes'] = used_codes
            save_data(data)
            bot.send_message(chat_id, f"✅ تم تفعيل الاشتراك لمدة {duration_days} يومًا!")
        else:
            bot.send_message(chat_id, "❌ الكود غير صحيح. حاول مرة أخرى أو تواصل مع الدعم.")
    except Exception as e:
        logger.error(f"خطأ في معالجة الكود: {e}")

# معالجة زر التحقق من الاشتراك
@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def check_subscription_callback(call):
    try:
        chat_id = call.message.chat.id
        if str(chat_id) in subscriptions and subscriptions[str(chat_id)]['active']:
            expiry_date = datetime.strptime(subscriptions[str(chat_id)]['expiry_date'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() <= expiry_date:
                days_left = (expiry_date - datetime.now()).days
                bot.send_message(chat_id, f"✅ اشتراكك نشط. متبقي {days_left} يومًا.")
            else:
                bot.send_message(chat_id, "⏰ انتهى اشتراكك. يرجى التجديد للمتابعة.")
        else:
            bot.send_message(chat_id, "❌ لست مشتركًا. استخدم كودًا لتفعيل اشتراكك.")
    except Exception as e:
        logger.error(f"خطأ في التحقق من الاشتراك: {e}")

# لوحة التحكم الإدارية
@bot.message_handler(commands=['admin'])
def send_control_panel(message):
    try:
        chat_id = message.chat.id
        if chat_id == OWNER_CHAT_ID:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn_add_codes = types.KeyboardButton('➕ إضافة أكواد')
            btn_show_codes = types.KeyboardButton('📋 عرض الأكواد')
            btn_broadcast_all = types.KeyboardButton('📢 إرسال للجميع')
            btn_broadcast_subs = types.KeyboardButton('📢 إرسال للمشتركين')
            markup.add(btn_add_codes, btn_show_codes)
            markup.add(btn_broadcast_all, btn_broadcast_subs)
            bot.send_message(chat_id, "🛠 لوحة التحكم الإدارية:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "🔒 هذا الأمر مخصص للمدير فقط.")
    except Exception as e:
        logger.error(f"خطأ في لوحة التحكم الإدارية: {e}")

@bot.message_handler(func=lambda message: message.text == '➕ إضافة أكواد' and message.chat.id == OWNER_CHAT_ID)
def add_codes_prompt(message):
    try:
        msg = bot.reply_to(message, "أدخل الأكواد والمدة (بالأيام) بالصيغة: كود1:مدة1,كود2:مدة2")
        bot.register_next_step_handler(msg, save_codes)
    except Exception as e:
        logger.error(f"خطأ في طلب إضافة الأكواد: {e}")

def save_codes(message):
    try:
        code_list = message.text.split(',')
        for item in code_list:
            code, duration = item.split(':')
            codes[code.strip()] = {'duration': int(duration.strip()), 'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        data['codes'] = codes
        save_data(data)
        bot.send_message(message.chat.id, "✅ تم إضافة الأكواد بنجاح!")
    except Exception as e:
        logger.error(f"خطأ في إضافة الأكواد: {e}")
        bot.send_message(message.chat.id, f"❌ خطأ في إضافة الأكواد: {e}")

@bot.message_handler(func=lambda message: message.text == '📋 عرض الأكواد' and message.chat.id == OWNER_CHAT_ID)
def show_codes(message):
    try:
        chat_id = message.chat.id
        if not codes and not used_codes:
            bot.send_message(chat_id, "📭 لا توجد أكواد متاحة.")
            return

        active_codes = "\n".join([f"الكود: {code}، المدة: {info['duration']} يومًا، تاريخ الإنشاء: {info['created_at']}" for code, info in codes.items()])
        used_codes_str = "\n".join([f"الكود: {code}" for code in used_codes])
        
        markup = types.InlineKeyboardMarkup()
        btn_clear_active = types.InlineKeyboardButton('🗑 حذف الأكواد النشطة', callback_data='clear_active_codes')
        btn_clear_used = types.InlineKeyboardButton('🗑 حذف الأكواد المستخدمة', callback_data='clear_used_codes')
        markup.add(btn_clear_active, btn_clear_used)

        bot.send_message(chat_id, f"📋 الأكواد النشطة:\n{active_codes or 'لا يوجد'}\n\n📋 الأكواد المستخدمة:\n{used_codes_str or 'لا يوجد'}", reply_markup=markup)
    except Exception as e:
        logger.error(f"خطأ في عرض الأكواد: {e}")

@bot.callback_query_handler(func=lambda call: call.data in ['clear_active_codes', 'clear_used_codes'])
def clear_codes_callback(call):
    try:
        if call.message.chat.id == OWNER_CHAT_ID:
            if call.data == 'clear_active_codes':
                codes.clear()
                data['codes'] = codes
                save_data(data)
                bot.send_message(call.message.chat.id, "✅ تم حذف الأكواد النشطة.")
            elif call.data == 'clear_used_codes':
                used_codes.clear()
                data['used_codes'] = used_codes
                save_data(data)
                bot.send_message(call.message.chat.id, "✅ تم حذف الأكواد المستخدمة.")
    except Exception as e:
        logger.error(f"خطأ في حذف الأكواد: {e}")

@bot.message_handler(func=lambda message: message.text == '📢 إرسال للجميع' and message.chat.id == OWNER_CHAT_ID)
def broadcast_all_prompt(message):
    try:
        msg = bot.reply_to(message, "أدخل الرسالة لإرسالها لجميع المستخدمين:")
        bot.register_next_step_handler(msg, broadcast_all)
    except Exception as e:
        logger.error(f"خطأ في طلب الإرسال للجميع: {e}")

def broadcast_all(message):
    try:
        text = message.text
        for chat_id in users:
            send_notification(chat_id, text)
        bot.send_message(message.chat.id, "✅ تم إرسال الرسالة لجميع المستخدمين.")
    except Exception as e:
        logger.error(f"خطأ في الإرسال للجميع: {e}")

@bot.message_handler(func=lambda message: message.text == '📢 إرسال للمشتركين' and message.chat.id == OWNER_CHAT_ID)
def broadcast_subs_prompt(message):
    try:
        msg = bot.reply_to(message, "أدخل الرسالة لإرسالها للمشتركين:")
        bot.register_next_step_handler(msg, broadcast_subs)
    except Exception as e:
        logger.error(f"خطأ في طلب الإرسال للمشتركين: {e}")

def broadcast_subs(message):
    try:
        text = message.text
        for chat_id in subscriptions:
            if subscriptions[chat_id]['active']:
                send_notification(chat_id, text)
        bot.send_message(message.chat.id, "✅ تم إرسال الرسالة لجميع المشتركين.")
    except Exception as e:
        logger.error(f"خطأ في الإرسال للمشتركين: {e}")

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

# التحقق من الاشتراكات المنتهية
def check_subscriptions():
    while True:
        try:
            now = datetime.now()
            for user_id in list(subscriptions.keys()):
                if subscriptions[user_id]['active']:
                    expiry_date = datetime.strptime(subscriptions[user_id]['expiry_date'], '%Y-%m-%d %H:%M:%S')
                    time_left = expiry_date - now
                    
                    # إرسال تذكير قبل يوم من انتهاء الاشتراك
                    if timedelta(days=0) < time_left <= timedelta(days=1):
                        send_notification(user_id, "⏰ اشتراكك سينتهي خلال أقل من 24 ساعة. جدد الآن!")
                    
                    # معالجة الاشتراكات المنتهية
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
            time.sleep(10)  # التحقق كل ساعة
        except Exception as e:
            logger.error(f"خطأ في فحص الاشتراكات: {e}")
            time.sleep(60)  # إعادة المحاولة بعد دقيقة في حالة الخطأ

# إعادة تشغيل البوت تلقائيًا في حالة التوقف
def run_bot():
    global bot  # إعلان bot كمتغير عالمي
    while True:
        try:
            logger.info("بدء تشغيل البوت...")
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            logger.error(f"خطأ في تشغيل البوت: {e}")
            time.sleep(100)  # الانتظار 10 ثوان قبل إعادة المحاولة
            try:
                # محاولة إعادة إنشاء البوت في حالة فشل الاتصال
                bot = telebot.TeleBot(API_TOKEN)
                logger.info("تم إعادة إنشاء كائن البوت")
            except Exception as e:
                logger.error(f"خطأ في إعادة إنشاء البوت: {e}")
            continue

# بدء خيط الخلفية لفحص الاشتراكات
threading.Thread(target=check_subscriptions, daemon=True).start()

# تشغيل البوت
if __name__ == "__main__":
    server()
    run_bot()
