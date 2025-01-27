import time
import requests
from bs4 import BeautifulSoup
import telebot
from flask import Flask, request

from app6 import server
# مفتاح API الخاص ببوت تليجرام
API_TOKEN = "5541021973:AAEEQRXxgcf7DY9LVVPrJxuOevv1MFeL87c"
CHAT_ID = "1916623948"

bot = telebot.TeleBot(API_TOKEN)

# مجموعة لتتبع المشاريع التي تم إرسال إشعار بها
sent_projects = set()

def fetch_projects():
    url = "https://mostaql.com/projects"  # رابط صفحة المشاريع
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        # استخراج العناوين من العناصر المناسبة
        projects = soup.find_all("h2", class_="mrg--bt-reset")
        for project in projects:
            title_tag = project.find("a")  # استخراج الرابط النصي
            if title_tag:
                title = title_tag.text.strip()
                link = title_tag["href"]
                project_id = link.split('/')[-1]  # استخراج معرف المشروع
                
                if "تليجرام" in title and project_id not in sent_projects:  # التحقق من الكلمة ومعرف المشروع
                    full_link = f"https://mostaql.com{link}"
                    message = f"📢 مشروع جديد متاح: {title}\nرابط المشروع: {full_link}"
                    send_telegram_notification(message)
                    sent_projects.add(project_id)  # إضافة المشروع إلى القائمة
    else:
        print("تعذر الوصول إلى موقع مستقل")

def send_telegram_notification(message):
    try:
        bot.send_message(CHAT_ID, message)
        print("تم إرسال الإشعار إلى تليجرام.")
    except Exception as e:
        print(f"خطأ في الإرسال إلى تليجرام: {e}")

def main():
    while True:
        fetch_projects()
        time.sleep(1000)  # انتظار دقيقة قبل إعادة المحاولة

if __name__ == "__main__":
    server()
    main()
