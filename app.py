#!/usr/bin/env python3
"""
🎬 FTGamer Premium Bot - WEBHOOK EDITION
👨💻 Developer: @ftgamer2
📢 Channel: https://t.me/ftgamer2
"""

import os
import logging
import tempfile
import shutil
import json
from datetime import datetime
import yt_dlp
from flask import Flask, request, jsonify

# Use pyTelegramBotAPI instead (simpler for webhook)
import telebot
from telebot import types

# ========== CONFIGURATION ==========
TOKEN = os.environ.get("BOT_TOKEN", "8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU")
PORT = int(os.environ.get("PORT", 8080))
DEVELOPER = "@ftgamer2"
CHANNEL = "https://t.me/ftgamer2"
WEBHOOK_URL = "https://impossible-philippe-ftgamerv2-477c9a71.koyeb.app"
# ===================================

# Initialize
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== EMOJI SYSTEM ==========
EMOJI = {
    'success': '✅', 'error': '❌', 'warning': '⚠️', 'loading': '⏳',
    'download': '📥', 'video': '🎬', 'audio': '🎵', 'rocket': '🚀',
    'fire': '🔥', 'heart': '❤️', 'star': '⭐', 'sparkle': '✨',
    '1080': '💎', '720': '📺', '480': '📱', '360': '🎯',
    'best': '🏆', 'cancel': '❌', 'stats': '📊'
}

# ========== QUALITY SETTINGS ==========
QUALITY_CONFIG = {
    '1080': {'name': '1080p FULL HD', 'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'},
    '720': {'name': '720p HD', 'format': 'bestvideo[height=720]+bestaudio/best[height=720]'},
    '480': {'name': '480p SD', 'format': 'bestvideo[height=480]+bestaudio/best[height=480]'},
    '360': {'name': '360p', 'format': 'bestvideo[height=360]+bestaudio/best[height=360]'},
    'best': {'name': 'BEST QUALITY', 'format': 'best'},
    'audio': {'name': 'AUDIO ONLY', 'format': 'bestaudio/best'}
}

# ========== STORAGE ==========
user_sessions = {}
download_stats = {
    'total': 0,
    'today': 0,
    'users': set(),
    'last_reset': datetime.now().date()
}

# ========== TELEGRAM HANDLERS ==========
@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """Handle /start command"""
    user_id = message.from_user.id
    download_stats['users'].add(user_id)
    
    welcome_text = f"""
{EMOJI['rocket']} <b>WELCOME TO FTGAMER PREMIUM</b> {EMOJI['rocket']}

{EMOJI['success']} <b>ALL FEATURES ACTIVE</b>
• YouTube Video Downloader
• Multiple Quality Support
• Audio Extraction (MP3)
• 24/7 Cloud Processing
• No Limits - No Ads

{EMOJI['download']} <b>HOW TO USE</b>
1. Send YouTube link
2. Select quality
3. Download instantly!

{EMOJI['stats']} <b>Bot Statistics:</b>
• Total Downloads: {download_stats['total']}
• Active Users: {len(download_stats['users'])}
• Status: ✅ ONLINE

{EMOJI['heart']} <b>Developer:</b> {DEVELOPER}
{EMOJI['link']} <b>Channel:</b> {CHANNEL}
"""
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML")

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    """Handle /stats command"""
    stats_text = f"""
{EMOJI['stats']} <b>BOT STATISTICS</b>

{EMOJI['download']} <b>Download Stats</b>
• Total Downloads: {download_stats['total']}
• Today's Downloads: {download_stats['today']}
• Active Users: {len(download_stats['users'])}

{EMOJI['user']} <b>Your Info</b>
• User ID: <code>{message.from_user.id}</code>
• Status: Premium User

{EMOJI['success']} <b>System Status</b>
• Server: Koyeb Cloud
• Uptime: 100%
• Mode: Webhook

{EMOJI['fire']} Ready for downloads!
"""
    bot.send_message(message.chat.id, stats_text, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and ('youtube.com' in m.text or 'youtu.be' in m.text))
def handle_youtube(message):
    """Handle YouTube links"""
    url = message.text.strip()
    chat_id = message.chat.id
    
    # Store URL
    user_sessions[chat_id] = {'url': url}
    
    # Create keyboard
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    markup.add(
        types.InlineKeyboardButton(f"{EMOJI['1080']} 1080p", callback_data="quality_1080"),
        types.InlineKeyboardButton(f"{EMOJI['720']} 720p", callback_data="quality_720"),
        types.InlineKeyboardButton(f"{EMOJI['480']} 480p", callback_data="quality_480")
    )
    
    markup.add(
        types.InlineKeyboardButton(f"{EMOJI['audio']} Audio", callback_data="quality_audio"),
        types.InlineKeyboardButton(f"{EMOJI['best']} Best", callback_data="quality_best"),
        types.InlineKeyboardButton(f"{EMOJI['360']} 360p", callback_data="quality_360")
    )
    
    markup.add(
        types.InlineKeyboardButton(f"{EMOJI['cancel']} Cancel", callback_data="cancel")
    )
    
    bot.send_message(
        chat_id,
        f"{EMOJI['success']} <b>LINK DETECTED!</b>\n\n"
        f"{EMOJI['download']} <b>Select download quality:</b>",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.message_handler(func=lambda m: True)
def handle_other(message):
    """Handle other messages"""
    help_text = f"""
{EMOJI['info']} <b>HOW TO USE</b>

Send me a YouTube link to download.

{EMOJI['star']} <b>Example:</b>
<code>https://youtube.com/watch?v=...</code>
<code>https://youtu.be/...</code>

{EMOJI['fire']} <b>All features are FREE!</b>
"""
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle callback queries"""
    chat_id = call.message.chat.id
    data = call.data
    
    bot.answer_callback_query(call.id)
    
    if data == 'cancel':
        bot.edit_message_text(
            f"{EMOJI['error']} <b>OPERATION CANCELLED</b>\n\n"
            f"{EMOJI['download']} Send another link when ready!",
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )
        return
    
    if data.startswith('quality_'):
        quality = data.replace('quality_', '')
        
        # Get URL
        url = user_sessions.get(chat_id, {}).get('url', '')
        
        if not url:
            bot.edit_message_text(
                f"{EMOJI['error']} <b>URL NOT FOUND</b>\n\n"
                f"Please send the link again.",
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
            return
        
        # Update stats
        download_stats['total'] += 1
        download_stats['today'] += 1
        
        # Start download
        import threading
        thread = threading.Thread(
            target=download_video,
            args=(url, quality, chat_id, call.message.message_id)
        )
        thread.start()
        
        # Show processing message
        bot.edit_message_text(
            f"{EMOJI['loading']} <b>STARTING DOWNLOAD...</b>\n\n"
            f"Quality: {QUALITY_CONFIG[quality]['name']}\n"
            f"Please wait 30-60 seconds...",
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )

def download_video(url, quality, chat_id, message_id):
    """Download video function"""
    try:
        # Send processing message
        msg = bot.send_message(
            chat_id,
            f"{EMOJI['loading']} <b>PREPARING DOWNLOAD...</b>\n\n"
            f"Fetching video information...",
            parse_mode="HTML"
        )
        
        # Get video info
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')[:50]
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')
        
        # Update with info
        bot.edit_message_text(
            f"{EMOJI['video']} <b>VIDEO INFORMATION</b>\n\n"
            f"📹 <b>Title:</b> {title}\n"
            f"👤 <b>Channel:</b> {uploader[:30]}\n"
            f"⏱️ <b>Duration:</b> {duration//60}:{duration%60:02d}\n"
            f"🎬 <b>Quality:</b> {QUALITY_CONFIG[quality]['name']}\n\n"
            f"{EMOJI['download']} Starting download...",
            chat_id=chat_id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(id)s_%(title)s.%(ext)s')
        
        # yt-dlp options (optimized for YouTube)
        ydl_opts = {
            'format': QUALITY_CONFIG[quality]['format'],
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],
                    'player_client': ['android', 'web'],
                }
            },
        }
        
        if quality == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            
            # Handle audio extension
            if quality == 'audio':
                downloaded_file = downloaded_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            # Find actual file
            if not os.path.exists(downloaded_file):
                base = os.path.splitext(downloaded_file)[0]
                for ext in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a']:
                    if os.path.exists(base + ext):
                        downloaded_file = base + ext
                        break
        
        if not os.path.exists(downloaded_file):
            raise Exception("File not found after download")
        
        # Get file size
        file_size = os.path.getsize(downloaded_file)
        file_size_mb = file_size / (1024 * 1024)
        
        # Send file
        with open(downloaded_file, 'rb') as file:
            if quality == 'audio' or downloaded_file.endswith('.mp3'):
                bot.send_audio(
                    chat_id=chat_id,
                    audio=file,
                    caption=f"🎵 <b>{title}</b>\n\n"
                           f"✅ Download Complete!\n"
                           f"📦 Size: {file_size_mb:.1f}MB\n"
                           f"🎶 Quality: 192kbps MP3\n\n"
                           f"⬇️ @ftgamer2_bot\n"
                           f"👤 {DEVELOPER}",
                    parse_mode="HTML"
                )
            else:
                bot.send_video(
                    chat_id=chat_id,
                    video=file,
                    caption=f"🎬 <b>{title}</b>\n\n"
                           f"✅ Download Complete!\n"
                           f"📦 Size: {file_size_mb:.1f}MB\n"
                           f"🎬 Quality: {QUALITY_CONFIG[quality]['name']}\n\n"
                           f"⬇️ @ftgamer2_bot\n"
                           f"👤 {DEVELOPER}",
                    parse_mode="HTML",
                    supports_streaming=True
                )
        
        # Success message
        bot.edit_message_text(
            f"{EMOJI['success']} <b>DOWNLOAD COMPLETE!</b>\n\n"
            f"📹 {title}\n"
            f"📦 {file_size_mb:.1f}MB\n"
            f"🎬 {QUALITY_CONFIG[quality]['name']}\n\n"
            f"{EMOJI['heart']} Thank you for using FTGamer!",
            chat_id=chat_id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )
        
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        
        error_msg = str(e)
        if "Sign in" in error_msg or "confirm" in error_msg:
            error_msg = "YouTube requires verification. Try:\n• Different video\n• Audio only\n• Lower quality"
        
        bot.send_message(
            chat_id,
            f"{EMOJI['error']} <b>DOWNLOAD FAILED</b>\n\n"
            f"Error: {error_msg[:100]}\n\n"
            f"Try:\n• Lower quality (720p/480p)\n• Audio only\n• Different video",
            parse_mode="HTML"
        )

# ========== FLASK ROUTES ==========
@app.route('/')
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>🎬 FTGamer Premium Bot</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 50px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        h1 {
            font-size: 3em;
            margin-bottom: 20px;
        }
        .emoji {
            font-size: 4em;
            margin: 20px;
            animation: bounce 2s infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .btn {
            display: inline-block;
            background: white;
            color: #667eea;
            padding: 15px 30px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: bold;
            margin: 10px;
            transition: transform 0.3s;
        }
        .btn:hover {
            transform: translateY(-3px);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="emoji">🎬</div>
        <h1>FTGamer Premium Bot</h1>
        <p>YouTube Video Downloader with Premium Features</p>
        <p>
            <a href="https://t.me/ftgamer2_bot" class="btn">🤖 Start Bot</a>
            <a href="https://t.me/ftgamer2" class="btn">📢 Join Channel</a>
        </p>
        <p style="margin-top: 40px; opacity: 0.8;">
            Developed by @ftgamer2<br>
            Running on Koyeb Cloud
        </p>
    </div>
</body>
</html>
"""

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'ftgamer-bot',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return ''

@app.route('/setwebhook')
def set_webhook():
    """Set webhook endpoint"""
    try:
        # Remove any existing webhook first
        import requests
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
        
        # Set new webhook
        webhook_url = f"{WEBHOOK_URL}/webhook"
        response = requests.get(f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}")
        
        return jsonify({
            'success': True,
            'message': 'Webhook set successfully',
            'webhook_url': webhook_url,
            'response': response.json()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ========== MAIN ==========
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎬 FTGAMER PREMIUM BOT - WEBHOOK EDITION")
    print("✨ Bot is ready to receive webhook requests")
    print("👨💻 Developer: @ftgamer2")
    print("🌐 Host: Koyeb Cloud")
    print("="*60)
    print(f"✅ Webhook URL: {WEBHOOK_URL}/webhook")
    print(f"✅ Health Check: {WEBHOOK_URL}/health")
    print(f"✅ Set Webhook: {WEBHOOK_URL}/setwebhook")
    print("="*60)
    print("🚀 Bot is running! Send /start to your bot")
    print("="*60)
    
    # Start Flask
    app.run(host='0.0.0.0', port=PORT, debug=False)