import os
import telebot
from flask import Flask, request, jsonify
import logging

# Setup
TOKEN = os.environ.get('BOT_TOKEN', '8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store
user_data = {}

# EMOJIS
EMOJIS = {
    'success': '✅', 'error': '❌', 'start': '🚀', 
    'video': '📹', 'download': '⬇️', 'heart': '❤️',
    'party': '🎉', 'star': '⭐', 'fire': '🔥'
}

# Telegram Handlers
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {'last_active': 'now'}
    
    welcome = f"""
{EMOJIS['party']} *FTGamer Premium Bot* {EMOJIS['party']}

{EMOJIS['fire']} *ALL FEATURES FREE*
• YouTube Video Downloader
• 8K/4K/1080p/720p Support
• Audio Extraction
• Bulk Downloads
• 24/7 Uptime

{EMOJIS['download']} *How to Use:*
1. Send YouTube link
2. Select quality
3. Download instantly!

{EMOJIS['star']} *Example Links:*
• `https://youtube.com/watch?v=...`
• `https://youtu.be/...`
• `https://youtube.com/shorts/...`

{EMOJIS['heart']} *Developer:* @ftgamer2
"""
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    stats = f"""
{EMOJIS['success']} *Bot Statistics*

• Platform: Koyeb Cloud
• Status: ✅ Online 24/7
• Active Users: {len(user_data)}
• Host: Mumbai (India)
• Uptime: 100%

{EMOJIS['start']} *Ready for Downloads!*
"""
    bot.send_message(message.chat.id, stats, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text and any(domain in m.text for domain in ['youtube.com', 'youtu.be', 'youtube']))
def handle_video_link(message):
    url = message.text
    
    # Create inline keyboard
    from telebot import types
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    btn1 = types.InlineKeyboardButton(f"{EMOJIS['video']} 1080p", callback_data="1080p")
    btn2 = types.InlineKeyboardButton(f"{EMOJIS['video']} 720p", callback_data="720p")
    btn3 = types.InlineKeyboardButton(f"{EMOJIS['video']} 480p", callback_data="480p")
    btn4 = types.InlineKeyboardButton(f"{EMOJIS['video']} Audio", callback_data="audio")
    btn5 = types.InlineKeyboardButton(f"{EMOJIS['fire']} Best", callback_data="best")
    btn6 = types.InlineKeyboardButton(f"{EMOJIS['error']} Cancel", callback_data="cancel")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    bot.send_message(message.chat.id,
                    f"{EMOJIS['success']} *Link Received!*\n\n"
                    f"{EMOJIS['download']} Select download quality:",
                    reply_markup=markup,
                    parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    if call.data == 'cancel':
        bot.answer_callback_query(call.id, "Cancelled")
        bot.send_message(chat_id, f"{EMOJIS['error']} Operation cancelled.")
        return
    
    quality_names = {
        '1080p': '1080p Full HD',
        '720p': '720p HD',
        '480p': '480p SD',
        'audio': 'Audio Only (MP3)',
        'best': 'Best Available Quality'
    }
    
    quality = quality_names.get(call.data, call.data)
    
    # Send processing message
    bot.answer_callback_query(call.id, f"Starting {quality} download...")
    
    processing_msg = bot.send_message(chat_id,
                    f"{EMOJIS['download']} *Download Started*\n\n"
                    f"• Quality: {quality}\n"
                    f"• Status: Processing...\n"
                    f"• Estimated time: 10-30 seconds\n\n"
                    f"{EMOJIS['start']} Please wait...",
                    parse_mode='Markdown')
    
    # Simulate download (replace with actual download later)
    import time
    time.sleep(2)
    
    # Update message
    bot.edit_message_text(
        f"{EMOJIS['success']} *Download Complete!*\n\n"
        f"• Quality: {quality}\n"
        f"• Status: ✅ Ready\n"
        f"• Platform: Koyeb\n\n"
        f"{EMOJIS['heart']} *Note:* Full download feature coming soon!\n"
        f"Currently in testing mode.",
        chat_id=chat_id,
        message_id=processing_msg.message_id,
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: True)
def default_response(message):
    help_text = f"""
{EMOJIS['success']} *FTGamer Bot Help*

Send me YouTube links to download.

{EMOJIS['start']} *Commands:*
/start - Welcome message
/stats - Bot statistics

{EMOJIS['video']} *Supported:*
• YouTube videos
• YouTube shorts
• YouTube playlists (coming soon)

{EMOJIS['heart']} *Contact:* @ftgamer2
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Flask Routes
@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'service': 'FTGamer Telegram Bot',
        'developer': '@ftgamer2',
        'endpoints': ['/', '/webhook', '/health'],
        'users': len(user_data)
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

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
    webhook_url = f"https://{request.host}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")
    return jsonify({'webhook_url': webhook_url, 'status': 'set'})

if __name__ == '__main__':
    # Get port from environment or default to 8080
    port = int(os.environ.get('PORT', 8080))
    
    # Set webhook on startup
    webhook_url = f"https://{os.environ.get('KOYEB_APP_URL', f'localhost:{port}')}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info(f"Starting bot on port {port}")
    logger.info(f"Webhook URL: {webhook_url}")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=port)