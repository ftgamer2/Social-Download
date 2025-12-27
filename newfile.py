import os
import telebot
from flask import Flask, request

# Bot token
TOKEN = "8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# EMOJIS
EMOJIS = {
    'success': '✅', 'error': '❌', 'start': '🚀', 'video': '📹'
}

# Simple bot handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
                    f"{EMOJIS['start']} FTGamer Bot is LIVE!\n\n"
                    f"{EMOJIS['success']} Send me a YouTube link to download.")

@bot.message_handler(func=lambda m: m.text and m.text.startswith('http'))
def handle_link(message):
    bot.send_message(message.chat.id, 
                    f"{EMOJIS['video']} Link received!\n\n"
                    f"Download options coming soon...")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.send_message(message.chat.id, 
                    "Send /start or a YouTube link.")

# Webhook handler
@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    # Get Koyeb app URL from environment
    url = os.getenv('KOYEB_APP_URL', 'https://your-app.koyeb.app')
    bot.set_webhook(url=url + '/' + TOKEN)
    return "✅ Webhook set! Bot is running on Koyeb."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))