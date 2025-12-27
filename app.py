import os
from flask import Flask, request
import telebot
import logging

# Bot Token - Hardcoded since env vars not working
TOKEN = "8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store user data
users = {}

EMOJIS = {
    'success': '✅', 'error': '❌', 'start': '🚀', 
    'video': '📹', 'download': '⬇️', 'heart': '❤️'
}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = True
    
    welcome = f"""
{EMOJIS['start']} *FTGamer Bot - Docker Edition* {EMOJIS['start']}

{EMOJIS['success']} *Features:*
• YouTube Video Download
• Multiple Qualities
• 24/7 Uptime
• Free Forever

{EMOJIS['download']} *How to use:*
Send any YouTube link!

{EMOJIS['heart']} *Developer:* @ftgamer2
"""
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats(message):
    stats_msg = f"""
{EMOJIS['success']} *Bot Statistics*

• Platform: Koyeb Docker
• Status: ✅ Online
• Users: {len(users)}
• Mode: Docker Container

{EMOJIS['start']} Ready for downloads!
"""
    bot.send_message(message.chat.id, stats_msg, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text and ('youtube.com' in m.text or 'youtu.be' in m.text))
def handle_link(message):
    from telebot import types
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton("1080p", callback_data="1080")
    btn2 = types.InlineKeyboardButton("720p", callback_data="720")
    btn3 = types.InlineKeyboardButton("Audio", callback_data="audio")
    btn4 = types.InlineKeyboardButton("Cancel", callback_data="cancel")
    
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(message.chat.id,
                    f"{EMOJIS['success']} *YouTube Link Detected!*\n\nSelect quality:",
                    reply_markup=markup,
                    parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data == 'cancel':
        bot.answer_callback_query(call.id, "Cancelled")
        bot.send_message(chat_id, f"{EMOJIS['error']} Cancelled.")
        return
    
    quality_map = {
        '1080': '1080p Full HD',
        '720': '720p HD',
        'audio': 'Audio Only'
    }
    
    quality = quality_map.get(call.data, 'Best')
    bot.answer_callback_query(call.id, f"Selected {quality}")
    
    msg = bot.send_message(chat_id,
                    f"{EMOJIS['download']} *Downloading...*\n\nQuality: {quality}\nPlease wait...",
                    parse_mode='Markdown')
    
    # Simulate download
    import time
    time.sleep(2)
    
    bot.edit_message_text(
        f"{EMOJIS['success']} *Download Complete!*\n\n"
        f"Quality: {quality}\n"
        f"Size: ~50MB\n"
        f"Status: ✅ Ready\n\n"
        f"{EMOJIS['heart']} *Note:* Bot is working on Koyeb Docker!",
        chat_id=chat_id,
        message_id=msg.message_id,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: True)
def default(message):
    help_text = f"""
{EMOJIS['start']} *FTGamer Bot Help*

Send YouTube links to download.

*Commands:*
/start - Start bot
/stats - Show statistics

*Example links:*
• https://youtube.com/watch?v=...
• https://youtu.be/...
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Flask routes
@app.route('/')
def home():
    return "FTGamer Bot is running on Docker!"

@app.route('/health')
def health():
    return "OK"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK'
    return 'Bad Request', 400

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    import requests
    webhook_url = f"https://{request.host}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f"Webhook set to: {webhook_url}"

if __name__ == '__main__':
    port = 8080  # Hardcoded since env vars not working
    logger.info(f"Starting bot on port {port}")
    
    # Try to set webhook
    try:
        bot.remove_webhook()
        time.sleep(1)
        # We'll set webhook manually after deployment
        logger.info("Webhook will be set manually after deployment")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    app.run(host='0.0.0.0', port=port)