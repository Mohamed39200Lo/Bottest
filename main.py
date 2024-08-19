from flask import Flask
import telebot
from threading import Thread


bot = telebot.TeleBot("7433644739:AAEVxiKNqqjdwwCuoAOpxkW0WRpWcjEpc1c")
app = Flask(__name__)

@app.route('/')
def ping():
    return "PONG !, HELLO FROM MTC"

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

def run():
    app.run(host='0.0.0.0', port=8080)

def server():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    server()
    bot.polling()
    
