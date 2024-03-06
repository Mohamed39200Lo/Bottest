import telebot
import subprocess
import gunicorn
bot = telebot.TeleBot('6502701693:AAEVzcAjLSnC23SkC8nSMWKUesYWTYxPTWo')

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "مرحبا تم ايقاف البوت موقتا")

@bot.message_handler(func=lambda message: True)
def reply_to_messages(message):
    if message.text == "السلام عليكم":
        bot.reply_to(message, "وعليكم السلام ورحمة الله وبركاته")
    elif message.text == "كيف الحال":
        bot.reply_to(message, "الحمد لله بخير")
    elif message.text == "من أي بلد أنت":
        bot.reply_to(message, "مصر")
subprocess.Popen(["gunicorn", "app:app", "-b", "0.0.0.0:8080"])
bot.polling()