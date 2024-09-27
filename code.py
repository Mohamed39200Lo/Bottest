import telebot
from telebot import types
from datetime import datetime, timedelta
import threading
from threading import Thread

import time
import json
from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def ping():
    return "PONG !, HELLO FROM MTC"




API_TOKEN = '7367224669:AAGa7WmrCOxn8JGm0jVOWHZezQDsyWJMAck'
bot = telebot.TeleBot(API_TOKEN)

# قائمة القنوات
channels = {
    '🌐 قناة التنبيهات': 'https://t.me/+wckuaDN7l5dmNTc0',
}

chanels = {
    'قناة 1': -1002222132008,
}

# تحميل البيانات من ملف JSON
def load_data():
    try:
        with open('data22.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# حفظ البيانات إلى ملف JSON
def save_data(data):
    with open('data22.json', 'w') as f:
        json.dump(data, f, indent=4, default=str)

# تحميل بيانات الاشتراكات والأكواد
data = load_data()
user_subscriptions = data.get('user_subscriptions', {})
one_month_codes = data.get('one_month_codes', [])
three_month_codes = data.get('three_month_codes', [])
used_codes = data.get('used_codes', [])
used_trials = data.get('used_trials', [])

# معرف مالك البوت
OWNER_CHAT_ID = 1103654418  # 

def save_subscription(chat_id, expiry_date):
    user_subscriptions[str(chat_id)] = {'expiry_date': expiry_date.strftime('%Y-%m-%d %H:%M:%S')}
    data['user_subscriptions'] = user_subscriptions
    save_data(data)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()

    btn_buy_codes = types.InlineKeyboardButton('شراء اكواد الاشتراك 🛒', url='https://wa.me/966575594911?text=انضمام-للبوت')
    btn_subscribe = types.InlineKeyboardButton('الاشتراك', callback_data='subscribe')
    btn_check_subscription = types.InlineKeyboardButton('التحقق من الاشتراك', callback_data='check_subscription')
    btn_support = types.InlineKeyboardButton('الدعم الفني', url='https://t.me/dezrt_vip')
    btn_free_trial = types.InlineKeyboardButton('تجربة مجانية', callback_data='free_trial')

    markup.add(btn_buy_codes)
    markup.add(btn_subscribe, btn_check_subscription)
    markup.add(btn_support, btn_free_trial)

    welcome_caption = data.get('welcome_caption', """مرحبًا بكم جميعًا في قروب ديزرت الVIP لمتابعة منتجات ديزرت!🚀
رسومنا رمزية الشهر  : 
10 ريال اشتراك شهر واحد ✅
25 ريال اشتراك ثلاث أشهر  ✅

خدماتنا :-
-نوفر لك تنبيهات بنفس اللحضه عند توفر المنتجات في الموقع✅
-خدمة نشتري لك من الموقع ✅

يسعدنا انضمامكم إلى هذا القروب المميز ( القناة الوحيدة في السعودية التي تقوم بالشراء عنك من موقع ديزرت )
 والتنبيهات تعمل على رصد منتجات ديزرت لحظة بلحظة كل ثانية ١ عند توفرها، وهذا مايميزنا 🌪️
قام فريقنا بتطوير بوت خاص يضمن لكم الحصول على أحدث الإشعارات والتحديثات فور توفر المنتجات، حتى تتمكنوا من الشراء كل يوم واقتناص الفرص المميزة من بين جميع القروبات و المتابعين .

شكراً لانضمامكم، ونتمنى لكم تجربة تسوق ممتعة وسهلة!

تحياتنا،
الادارة🫶🏻""")

    #with open('1000252417.png', 'rb') as photo:
    bot.send_message(chat_id, welcome_caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'free_trial')
def free_trial_callback(call):
    chat_id = call.message.chat.id
    
    if str(chat_id) in user_subscriptions:
        bot.send_message(chat_id, "أنت مشترك بالفعل، لا يمكنك استخدام التجربة المجانية.")
    elif chat_id in used_trials:
        bot.send_message(chat_id, "لقد استخدمت التجربة المجانية بالفعل.")
    else:
        expiry_date = datetime.now() + timedelta(days=1)
        user_subscriptions[str(chat_id)] = {'expiry_date': expiry_date}
        save_subscription(chat_id, expiry_date)
        used_trials.append(chat_id)
        data['used_trials'] = used_trials
        save_data(data)
        bot.send_message(chat_id, "تم تفعيل تجربتك المجانية لمدة 24 ساعة من الآن!")
        send_channels(chat_id)

@bot.message_handler(commands=['welcome'])
def set_welcome_caption(message):
    if message.chat.id == OWNER_CHAT_ID:
        msg = bot.reply_to(message, "يرجى إدخال الرسالة الترحيبية الجديدة:")
        bot.register_next_step_handler(msg, save_welcome_caption)
    else:
        bot.send_message(message.chat.id, "عذرًا، هذه الأوامر مخصصة فقط لمالك البوت.")

def save_welcome_caption(message):
    data['welcome_caption'] = message.text
    save_data(data)
    bot.send_message(message.chat.id, "تم تحديث الرسالة الترحيبية بنجاح!")

@bot.callback_query_handler(func=lambda call: call.data == 'subscribe')
def subscribe_callback(call):
    msg = bot.send_message(call.message.chat.id, "يرجى إدخال كود الاشتراك:")
    bot.register_next_step_handler(msg, process_code)

@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def check_subscription_callback(call):
    chat_id = call.message.chat.id
    if str(chat_id) in user_subscriptions:
        expiry_date = datetime.strptime(user_subscriptions[str(chat_id)]['expiry_date'], '%Y-%m-%d %H:%M:%S')
        days_left = (expiry_date - datetime.now()).days
        bot.send_message(chat_id, f"أنت مشترك ويتبقى {days_left} أيام على انتهاء الاشتراك.")
    else:
        bot.send_message(chat_id, "أنت لست مشتركًا حالياً.")

# لوحة التحكم 
@bot.message_handler(commands=['control'])
def send_control_panel(message):
    chat_id = message.chat.id
    if chat_id == OWNER_CHAT_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_month_codes = types.KeyboardButton('أكواد الشهر')
        btn_three_month_codes = types.KeyboardButton('أكواد 3 أشهر')
        btn_show_codes = types.KeyboardButton('عرض الأكواد')
        btn_broadcast = types.KeyboardButton('إرسال رسالة للمشتركين')
        markup.add(btn_month_codes, btn_three_month_codes, btn_show_codes)
        markup.add(btn_broadcast)
        bot.send_message(chat_id, "اختر أحد الخيارات للتحكم بالأكواد:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "عذرًا، هذه الأوامر مخصصة فقط لمالك البوت.")

@bot.message_handler(func=lambda message: message.text == 'أكواد الشهر' and message.chat.id == OWNER_CHAT_ID)
def get_month_codes(message):
    msg = bot.reply_to(message, "يرجى إدخال أكواد الشهر مفصولة بفواصل:")
    bot.register_next_step_handler(msg, save_month_codes)

def save_month_codes(message):
    codes = message.text.split(',')
    one_month_codes.extend(int(code.strip()) for code in codes if code.strip().isdigit())
    data['one_month_codes'] = one_month_codes
    save_data(data)
    bot.send_message(message.chat.id, "تم حفظ أكواد الشهر بنجاح!")

@bot.message_handler(func=lambda message: message.text == 'أكواد 3 أشهر' and message.chat.id == OWNER_CHAT_ID)
def get_three_month_codes(message):
    msg = bot.reply_to(message, "يرجى إدخال أكواد 3 أشهر مفصولة بفواصل:")
    bot.register_next_step_handler(msg, save_three_month_codes)

def save_three_month_codes(message):
    codes = message.text.split(',')
    three_month_codes.extend(int(code.strip()) for code in codes if code.strip().isdigit())
    data['three_month_codes'] = three_month_codes
    save_data(data)
    bot.send_message(message.chat.id, "تم حفظ أكواد 3 أشهر بنجاح!")

@bot.message_handler(func=lambda message: message.text == 'عرض الأكواد' and message.chat.id == OWNER_CHAT_ID)
def show_codes(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    btn_clear_month = types.InlineKeyboardButton('حذف أكواد الشهر', callback_data='clear_month_codes')
    btn_clear_three_month = types.InlineKeyboardButton('حذف أكواد 3 أشهر', callback_data='clear_three_month_codes')
    markup.add(btn_clear_month, btn_clear_three_month)
    bot.send_message(chat_id, f"أكواد الشهر: {one_month_codes}\nأكواد 3 أشهر: {three_month_codes}\nأكواد مستخدمة: {used_codes}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['clear_month_codes', 'clear_three_month_codes'])
def clear_codes(call):
    if call.message.chat.id == OWNER_CHAT_ID:
        if call.data == 'clear_month_codes':
            one_month_codes.clear()
            data['one_month_codes'] = one_month_codes
            save_data(data)
            bot.send_message(call.message.chat.id, "تم حذف أكواد الشهر بنجاح!")
        elif call.data == 'clear_three_month_codes':
            three_month_codes.clear()
            data['three_month_codes'] = three_month_codes
            save_data(data)
            bot.send_message(call.message.chat.id, "تم حذف أكواد 3 أشهر بنجاح!")

@bot.message_handler(func=lambda message: message.text == 'إرسال رسالة للمشتركين' and message.chat.id == OWNER_CHAT_ID)
def broadcast_message_prompt(message):
    msg = bot.reply_to(message, "يرجى إدخال الرسالة التي تريد إرسالها:")
    bot.register_next_step_handler(msg, broadcast_message)

def broadcast_message(message):
    text = message.text
    for chat_id in user_subscriptions.keys():
        try:
            bot.send_message(chat_id, text)
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
    bot.send_message(message.chat.id, "تم إرسال الرسالة لجميع المشتركين بنجاح!")

def send_channels(chat_id):
    for ch_name, ch_link in channels.items():
        bot.send_message(chat_id, f"يرجى الانضمام إلى {ch_name}: {ch_link}")

def process_code(message):
    chat_id = message.chat.id
    code = int(message.text.strip())

    if code in used_codes:
        bot.send_message(chat_id, "هذا الكود مستخدم من قبل.")
    elif code in one_month_codes:
        expiry_date = datetime.now() + timedelta(days=30)
        save_subscription(chat_id, expiry_date)
        one_month_codes.remove(code)
        used_codes.append(code)
        data['one_month_codes'] = one_month_codes
        data['used_codes'] = used_codes
        save_data(data)
        bot.send_message(chat_id, "تم الاشتراك لمدة شهر بنجاح!")
        send_channels(chat_id)
    elif code in three_month_codes:
        expiry_date = datetime.now() + timedelta(days=90)
        save_subscription(chat_id, expiry_date)
        three_month_codes.remove(code)
        used_codes.append(code)
        data['three_month_codes'] = three_month_codes
        data['used_codes'] = used_codes
        save_data(data)
        bot.send_message(chat_id, "تم الاشتراك لمدة 3 أشهر بنجاح!")
        send_channels(chat_id)
    else:
        bot.send_message(chat_id, "الكود غير صحيح.")

@bot.chat_join_request_handler(func=lambda join_request: True)
def approve_join_request(join_request):
    user_id = join_request.from_user.id
    chat_id = join_request.chat.id

    # التحقق من وجود المستخدم في الاشتراكات
    if str(user_id) in user_subscriptions:
        # تحويل تاريخ انتهاء الاشتراك من نص إلى كائن datetime
        expiry_date_str = user_subscriptions[str(user_id)]['expiry_date']
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d %H:%M:%S')
        
        if datetime.now() <= expiry_date:
            bot.approve_chat_join_request(chat_id, user_id)
            bot.send_message(user_id, "تم قبول طلب انضمامك إلى القناة!")
        else:
            # حذف الاشتراك المنتهي
            del user_subscriptions[str(user_id)]
            data['user_subscriptions'] = user_subscriptions
            save_data(data)  # حفظ التغييرات في ملف JSON
            bot.send_message(user_id, "انتهى اشتراكك. يرجى تجديد اشتراكك للانضمام إلى القناة.")
    else:
        bot.send_message(user_id, "أنت لست مشتركًا. يرجى الاشتراك للانضمام إلى القناة.")

# إزالة الأعضاء من القنوات عند انتهاء الاشتراك
def check_expired_subscriptions():
    while True:
        now = datetime.now()
        for user_id, sub_info in list(user_subscriptions.items()):
            # تحويل تاريخ انتهاء الاشتراك من نص إلى كائن datetime
            expiry_date_str = sub_info['expiry_date']
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d %H:%M:%S')
            
            if now > expiry_date:
                # إذا انتهى الاشتراك، يتم إزالة المستخدم من القنوات
                for chanel in chanels.values():
                    try:
                        bot.kick_chat_member(chanel, int(user_id))  # تحويل user_id إلى int إذا كان في شكل نص
                        bot.unban_chat_member(chanel, int(user_id))  
                        bot.send_message(user_id,"انتهى اشتراكك يمكنك شراء الاكواد لاعادة الاشتراك مرة اخرى")
                    except Exception as e:
                        print(f"Error kicking user {user_id} from {chanel}: {e}")
                
                # التأكد من وجود user_id قبل حذفه
                try:
                    if user_id in user_subscriptions:
                        del user_subscriptions[user_id]
                    if str(user_id) in data:
                        del data[str(user_id)]
                except KeyError as e:
                    print(f"Error deleting user {user_id}: {e}")
        
        # حفظ التعديلات على البيانات في ملف JSON
        data['user_subscriptions'] = user_subscriptions
        save_data(data)
        print(55)
        
        time.sleep(10000)  # التحقق كل 9600 ثانية (حوالي 2.5 ساعة)

# بدء تشغيل التحقق في خيط منفصل
threading.Thread(target=check_expired_subscriptions).start()



def run():
    app.run(host='0.0.0.0', port=8080)

def server():
    t = Thread(target=run)
    t.start()

# بدء التنفيذ
if __name__ == "__main__":
    server()
    bot.polling()
