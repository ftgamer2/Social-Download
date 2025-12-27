import os
import telebot
from flask import Flask, request, jsonify
import logging
import yt_dlp
import tempfile
import shutil
from telebot import types
import threading
import time

# Bot Token
TOKEN = "8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store download progress
download_progress = {}

# EMOJIS
EMOJIS = {
    'success': '✅', 'error': '❌', 'start': '🚀', 
    'video': '📹', 'download': '⬇️', 'heart': '❤️',
    'party': '🎉', 'star': '⭐', 'fire': '🔥',
    'loading': '⏳', 'music': '🎵', 'cancel': '❌',
    '1080': '💎', '720': '📺', '480': '📱', '360': '⚡'
}

# Quality settings
QUALITY_FORMATS = {
    '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
    '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
    '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
    '360': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
    'audio': 'bestaudio/best',
    'best': 'best'
}

# ========== TELEGRAM HANDLERS ==========
@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    welcome = f"""
{EMOJIS['party']} *FTGamer Premium Bot* {EMOJIS['party']}

{EMOJIS['fire']} *ALL FEATURES ACTIVE*
• YouTube Video Downloader ✓
• Multiple Quality Support ✓
• Audio Extraction ✓
• 24/7 Uptime ✓
• Free Forever ✓

{EMOJIS['download']} *How to Use:*
1. Send YouTube link
2. Select quality
3. Download actual video!

{EMOJIS['star']} *Supported:*
• YouTube videos
• YouTube Shorts
• YouTube playlists
• Instagram (coming soon)
• TikTok (coming soon)

{EMOJIS['heart']} *Developer:* @ftgamer2
"""
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    stats = f"""
{EMOJIS['success']} *Bot Statistics*

• Platform: Koyeb Cloud
• Status: ✅ Online
• Service: Video Downloader
• Features: Full Working
• Storage: Temp Files

{EMOJIS['download']} *Ready for real downloads!*
"""
    bot.send_message(message.chat.id, stats, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text and ('youtube.com' in m.text or 'youtu.be' in m.text))
def handle_youtube(message):
    url = message.text
    chat_id = message.chat.id
    
    # Store URL for this chat
    download_progress[chat_id] = {'url': url, 'status': 'pending'}
    
    # Create quality selection keyboard
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    btn1 = types.InlineKeyboardButton(f"{EMOJIS['1080']} 1080p", callback_data=f"download_1080_{chat_id}")
    btn2 = types.InlineKeyboardButton(f"{EMOJIS['720']} 720p", callback_data=f"download_720_{chat_id}")
    btn3 = types.InlineKeyboardButton(f"{EMOJIS['480']} 480p", callback_data=f"download_480_{chat_id}")
    btn4 = types.InlineKeyboardButton(f"{EMOJIS['music']} Audio", callback_data=f"download_audio_{chat_id}")
    btn5 = types.InlineKeyboardButton(f"{EMOJIS['fire']} Best", callback_data=f"download_best_{chat_id}")
    btn6 = types.InlineKeyboardButton(f"{EMOJIS['cancel']} Cancel", callback_data=f"cancel_{chat_id}")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    bot.send_message(chat_id,
                    f"{EMOJIS['success']} *YouTube Link Detected!*\n\n"
                    f"{EMOJIS['download']} Select download quality:",
                    reply_markup=markup,
                    parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data.startswith('cancel_'):
        bot.answer_callback_query(call.id, "Cancelled")
        bot.send_message(chat_id, f"{EMOJIS['cancel']} Download cancelled.")
        return
    
    if data.startswith('download_'):
        # Extract quality and chat_id
        parts = data.split('_')
        quality = parts[1]
        target_chat_id = parts[2] if len(parts) > 2 else chat_id
        
        # Answer callback
        quality_names = {
            '1080': '1080p Full HD',
            '720': '720p HD',
            '480': '480p SD',
            'audio': 'Audio Only (MP3)',
            'best': 'Best Quality'
        }
        
        quality_name = quality_names.get(quality, quality)
        bot.answer_callback_query(call.id, f"Starting {quality_name} download...")
        
        # Get URL from progress store
        url = download_progress.get(target_chat_id, {}).get('url', '')
        
        if not url:
            bot.send_message(chat_id, f"{EMOJIS['error']} URL not found. Send link again.")
            return
        
        # Start download in background thread
        thread = threading.Thread(
            target=download_video,
            args=(url, quality, target_chat_id, call.message.message_id)
        )
        thread.start()
        
        # Send initial processing message
        msg = bot.send_message(
            target_chat_id,
            f"{EMOJIS['loading']} *Starting Download...*\n\n"
            f"• Quality: {quality_name}\n"
            f"• Status: Initializing...\n"
            f"• This may take 30-60 seconds",
            parse_mode='Markdown'
        )
        
        # Store message ID for updates
        download_progress[target_chat_id] = {
            'url': url,
            'status': 'downloading',
            'message_id': msg.message_id,
            'quality': quality
        }

# ========== ACTUAL VIDEO DOWNLOAD FUNCTION ==========
def download_video(url, quality, chat_id, original_msg_id):
    """Actual video download function"""
    try:
        # Update status
        temp_msg = bot.send_message(chat_id, f"{EMOJIS['loading']} Preparing download...")
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(title).50s.%(ext)s')
        
        # yt-dlp options
        ydl_opts = {
            'format': QUALITY_FORMATS.get(quality, 'best'),
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'progress_hooks': [lambda d: progress_hook(d, chat_id, temp_msg.message_id)],
        }
        
        if quality == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'postprocessor_args': ['-ar', '44100'],
            })
        
        # Extract video info first
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Video')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')
        
        # Update with video info
        bot.edit_message_text(
            f"{EMOJIS['download']} *Downloading...*\n\n"
            f"📹 *Title:* {video_title[:50]}\n"
            f"👤 *Channel:* {uploader[:30]}\n"
            f"⏱️ *Duration:* {duration//60}:{duration%60:02d}\n"
            f"📦 *Quality:* {quality}\n"
            f"⬇️ *Status:* Downloading...",
            chat_id=chat_id,
            message_id=temp_msg.message_id,
            parse_mode='Markdown'
        )
        
        # Start actual download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            
            # For audio downloads, file extension changes
            if quality == 'audio':
                downloaded_file = downloaded_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            # Check if file exists
            if not os.path.exists(downloaded_file):
                # Try to find the actual file
                base_name = os.path.splitext(downloaded_file)[0]
                for ext in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a']:
                    if os.path.exists(base_name + ext):
                        downloaded_file = base_name + ext
                        break
        
        # Get file size
        file_size = os.path.getsize(downloaded_file)
        file_size_mb = file_size / (1024 * 1024)
        
        # Send the actual file
        with open(downloaded_file, 'rb') as file:
            if quality == 'audio' or downloaded_file.endswith('.mp3'):
                bot.send_audio(
                    chat_id=chat_id,
                    audio=file,
                    caption=f"🎵 *{video_title[:50]}*\n\n"
                           f"✅ Download Complete!\n"
                           f"📦 Size: {file_size_mb:.1f}MB\n"
                           f"🎶 Quality: 192kbps MP3\n\n"
                           f"⬇️ @ftgamer2_bot",
                    parse_mode='Markdown'
                )
            else:
                bot.send_video(
                    chat_id=chat_id,
                    video=file,
                    caption=f"📹 *{video_title[:50]}*\n\n"
                           f"✅ Download Complete!\n"
                           f"📦 Size: {file_size_mb:.1f}MB\n"
                           f"🎬 Quality: {quality}\n\n"
                           f"⬇️ @ftgamer2_bot",
                    parse_mode='Markdown',
                    supports_streaming=True
                )
        
        # Send completion message
        bot.edit_message_text(
            f"{EMOJIS['success']} *Download Complete!*\n\n"
            f"📹 *Title:* {video_title[:50]}\n"
            f"📦 *Size:* {file_size_mb:.1f}MB\n"
            f"🎬 *Quality:* {quality}\n"
            f"✅ *Status:* Sent to chat!\n\n"
            f"{EMOJIS['heart']} Thank you for using FTGamer Bot!",
            chat_id=chat_id,
            message_id=temp_msg.message_id,
            parse_mode='Markdown'
        )
        
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        bot.send_message(
            chat_id,
            f"{EMOJIS['error']} *Download Failed*\n\n"
            f"Error: {str(e)[:100]}\n\n"
            f"Try:\n• Different quality\n• Different video\n• Try again later",
            parse_mode='Markdown'
        )

def progress_hook(d, chat_id, message_id):
    """Update download progress"""
    if d['status'] == 'downloading':
        try:
            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            
            # Update progress message every 10%
            if '_percent_str' in d:
                bot.edit_message_text(
                    f"{EMOJIS['download']} *Downloading...*\n\n"
                    f"📊 *Progress:* {percent}\n"
                    f"⚡ *Speed:* {speed}\n"
                    f"⏱️ *ETA:* {eta}\n"
                    f"⬇️ *Status:* Downloading...",
                    chat_id=chat_id,
                    message_id=message_id,
                    parse_mode='Markdown'
                )
        except:
            pass

# ========== FLASK ROUTES ==========
@app.route('/')
def home():
    return "FTGamer Video Downloader Bot - ACTUAL DOWNLOADS WORKING!"

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'video-downloader'})

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
    return jsonify({'webhook_url': webhook_url, 'status': 'set'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    # Set webhook on startup
    try:
        bot.remove_webhook()
        time.sleep(1)
        webhook_url = f"https://{os.environ.get('KOYEB_PUBLIC_DOMAIN', request.host)}/webhook"
        bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    
    logger.info(f"Starting bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)