import os
import telebot
from flask import Flask, request
import yt_dlp
import tempfile
import shutil
import threading

# Bot setup
TOKEN = "8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# EMOJIS
EMOJI = {
    'success': '✅', 'error': '❌', 'start': '🚀', 'video': '🎬',
    'download': '📥', 'heart': '❤️', 'loading': '⏳'
}

# Store user sessions
user_data = {}

# ========== TELEGRAM HANDLERS ==========
@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome = f"""
{EMOJI['start']} <b>FTGamer Premium Bot</b>

{EMOJI['success']} <b>Features:</b>
• YouTube Video Downloader
• Multiple Qualities (1080p to 360p)
• Audio Extraction
• Fast & Free

{EMOJI['download']} <b>How to use:</b>
Send any YouTube link!

Example:
<code>https://youtube.com/watch?v=...</code>
<code>https://youtu.be/...</code>

Developer: @ftgamer2
"""
    bot.reply_to(message, welcome)

@bot.message_handler(func=lambda m: m.text and ('youtube.com' in m.text or 'youtu.be' in m.text))
def handle_link(message):
    url = message.text
    user_data[message.chat.id] = {'url': url}
    
    from telebot import types
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    markup.add(
        types.InlineKeyboardButton("1080p", callback_data="quality_1080"),
        types.InlineKeyboardButton("720p", callback_data="quality_720"),
        types.InlineKeyboardButton("480p", callback_data="quality_480")
    )
    
    markup.add(
        types.InlineKeyboardButton("Audio", callback_data="quality_audio"),
        types.InlineKeyboardButton("Best", callback_data="quality_best"),
        types.InlineKeyboardButton("Cancel", callback_data="cancel")
    )
    
    bot.send_message(
        message.chat.id,
        f"{EMOJI['success']} <b>Link received!</b>\n\nSelect quality:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == 'cancel':
        bot.answer_callback_query(call.id, "Cancelled")
        bot.send_message(chat_id, f"{EMOJI['error']} Cancelled.")
        return
    
    if data.startswith('quality_'):
        quality = data.split('_')[1]
        url = user_data.get(chat_id, {}).get('url', '')
        
        if not url:
            bot.answer_callback_query(call.id, "No URL found")
            bot.send_message(chat_id, "Please send link again.")
            return
        
        bot.answer_callback_query(call.id, f"Starting {quality} download...")
        
        # Start download in background
        thread = threading.Thread(target=download_video, args=(chat_id, url, quality))
        thread.start()

def download_video(chat_id, url, quality):
    try:
        # Send processing message
        msg = bot.send_message(chat_id, f"{EMOJI['loading']} Downloading {quality}...")
        
        # Temp directory
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, 'video.%(ext)s')
        
        # yt-dlp options
        ydl_opts = {
            'format': 'best' if quality == 'best' else f'best[height<={quality}]',
            'outtmpl': output_path,
            'quiet': True,
        }
        
        if quality == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if quality == 'audio':
                filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
        
        # Send file
        with open(filename, 'rb') as f:
            if quality == 'audio':
                bot.send_audio(chat_id, f, caption=f"{EMOJI['success']} Audio downloaded!")
            else:
                bot.send_video(chat_id, f, caption=f"{EMOJI['success']} Video downloaded!")
        
        # Delete processing message
        bot.delete_message(chat_id, msg.message_id)
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        bot.send_message(chat_id, f"{EMOJI['error']} Error: {str(e)[:100]}")

# ========== FLASK ROUTES ==========
@app.route('/')
def home():
    return "FTGamer Bot is running!"

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

# ========== START POLLING IN BACKGROUND ==========
def start_polling():
    print("Starting bot in polling mode...")
    bot.polling(none_stop=True, interval=0, timeout=20)

# Start polling in background thread
import threading
poll_thread = threading.Thread(target=start_polling, daemon=True)
poll_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Bot starting on port {port}")
    app.run(host='0.0.0.0', port=port)