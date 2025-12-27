#!/usr/bin/env python3
"""
🎬 FTGamer Premium Downloader - ULTIMATE EDITION
✨ Features: Animated UI, Progress Bars, Real-time Updates, Premium Design
👨💻 Developer: @ftgamer2
📢 Channel: https://t.me/ftgamer2
"""

import os
import sys
import time
import json
import logging
import threading
import tempfile
import shutil
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import telebot
from telebot import types
import yt_dlp
import requests
from io import BytesIO
import random
import re

# ========== CONFIGURATION ==========
# ⚠️ WARNING: GO TO @BotFather AND REVOKE THIS TOKEN IMMEDIATELY FOR SECURITY
TOKEN = "8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU"
PORT = 8080
DEVELOPER = "@ftgamer2"
CHANNEL = "https://t.me/ftgamer2"
# ===================================

# Initialize
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# Setup advanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ========== EMOJI SYSTEM ==========
EMOJI = {
    'online': '🟢', 'offline': '🔴', 'loading': '🔄', 'success': '✅',
    'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'star': '⭐',
    'download': '📥', 'upload': '📤', 'process': '⚙️', 'search': '🔍',
    'convert': '🔄', 'compress': '🗜️', 'extract': '📂',
    'video': '🎬', 'audio': '🎵', 'photo': '🖼️', 'document': '📄',
    'link': '🔗', 'folder': '📁', 'cloud': '☁️',
    '8k': '👑', '4k': '🔥', '2k': '⚡', '1080': '💎',
    '720': '📺', '480': '📱', '360': '🎯', 'best': '🏆',
    'rocket': '🚀', 'fire': '🔥', 'heart': '❤️', 'sparkle': '✨',
    'trophy': '🏆', 'crown': '👑', 'diamond': '💎', 'bolt': '⚡',
    'clock': '⏰', 'calendar': '📅', 'bell': '🔔', 'lock': '🔒',
    'unlock': '🔓', 'settings': '⚙️', 'home': '🏠', 'back': '↩️',
    'youtube': '📺', 'instagram': '📷', 'tiktok': '🎵', 'facebook': '👤',
    'twitter': '🐦', 'telegram': '📱', 'whatsapp': '💬',
    'bar_start': '┏', 'bar_mid': '━', 'bar_end': '┓',
    'fill': '█', 'empty': '░',
    'spin1': '🌀', 'spin2': '⚪', 'spin3': '🔄',
    'wave1': '🌊', 'wave2': '💫', 'wave3': '✨',
    'stats': '📊', 'user': '👤'
}

# ========== QUALITY SETTINGS ==========
QUALITY_CONFIG = {
    '8k': {'name': '8K ULTRA HD', 'format': 'bestvideo[height>=4320]+bestaudio/best[height>=4320]', 'emoji': EMOJI['8k']},
    '4k': {'name': '4K ULTRA HD', 'format': 'bestvideo[height>=2160]+bestaudio/best[height>=2160]', 'emoji': EMOJI['4k']},
    '2k': {'name': '2K QHD', 'format': 'bestvideo[height>=1440]+bestaudio/best[height>=1440]', 'emoji': EMOJI['2k']},
    '1080': {'name': '1080p FULL HD', 'format': 'bestvideo[height<=1080][height>=720]+bestaudio/best[height<=1080]', 'emoji': EMOJI['1080']},
    '720': {'name': '720p HD', 'format': 'bestvideo[height=720]+bestaudio/best[height=720]', 'emoji': EMOJI['720']},
    '480': {'name': '480p SD', 'format': 'bestvideo[height=480]+bestaudio/best[height=480]', 'emoji': EMOJI['480']},
    '360': {'name': '360p', 'format': 'bestvideo[height=360]+bestaudio/best[height=360]', 'emoji': EMOJI['360']},
    'best': {'name': 'BEST QUALITY', 'format': 'bestvideo+bestaudio/best', 'emoji': EMOJI['best']},
    'audio': {'name': 'AUDIO ONLY', 'format': 'bestaudio/best', 'emoji': EMOJI['audio']}
}

# ========== STORAGE & SESSIONS ==========
user_sessions = {}
download_stats = {'total': 0, 'today': 0, 'size_gb': 0, 'users': set(), 'last_reset': datetime.now().date()}

# ========== ANIMATION FRAMES ==========
ANIMATION = {
    'spinner': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'dots': ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
    'moon': ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'],
    'hearts': ['💛', '💚', '💙', '💜', '❤️', '🧡'],
}

# ========== HELPER FUNCTIONS ==========
def reset_daily_stats():
    today = datetime.now().date()
    if today != download_stats['last_reset']:
        download_stats['today'] = 0
        download_stats['last_reset'] = today

def format_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0: return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def format_time(seconds):
    if seconds < 60: return f"{seconds:.0f}s"
    elif seconds < 3600: return f"{seconds/60:.0f}m {seconds%60:.0f}s"
    else: return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

def create_progress_bar(percentage, width=20):
    filled = int(width * percentage / 100)
    return EMOJI['bar_start'] + (EMOJI['fill'] * filled) + (EMOJI['empty'] * (width - filled)) + EMOJI['bar_end']

def get_spinner(index=0):
    return ANIMATION['spinner'][index % len(ANIMATION['spinner'])]

# ========== TELEGRAM UI COMPONENTS ==========
def create_welcome_message(user_id):
    reset_daily_stats()
    download_stats['users'].add(user_id)
    anim_index = int(time.time()) % len(ANIMATION['hearts'])
    return f"""
{EMOJI['sparkle']} <b>WELCOME TO FTGAMER PREMIUM</b> {EMOJI['sparkle']}

{EMOJI['rocket']} <b>ULTIMATE FEATURES UNLOCKED</b>
{EMOJI['success']} 8K/4K Video Downloads
{EMOJI['success']} Audio Extraction (MP3)
{EMOJI['success']} 24/7 Cloud Processing

{EMOJI['stats']} <b>BOT STATISTICS</b>
• Total Downloads: {download_stats['total']}
• Active Users: {len(download_stats['users'])}
• Total Data: {download_stats['size_gb']:.2f} GB

{EMOJI['heart']} <b>Developer:</b> {DEVELOPER}
{ANIMATION['hearts'][anim_index]} <i>Ready when you are!</i>
"""

def create_quality_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        types.InlineKeyboardButton(f"{EMOJI['8k']} 8K", callback_data="quality_8k"),
        types.InlineKeyboardButton(f"{EMOJI['4k']} 4K", callback_data="quality_4k"),
        types.InlineKeyboardButton(f"{EMOJI['2k']} 2K", callback_data="quality_2k")
    )
    keyboard.add(
        types.InlineKeyboardButton(f"{EMOJI['1080']} 1080p", callback_data="quality_1080"),
        types.InlineKeyboardButton(f"{EMOJI['720']} 720p", callback_data="quality_720"),
        types.InlineKeyboardButton(f"{EMOJI['480']} 480p", callback_data="quality_480")
    )
    keyboard.add(
        types.InlineKeyboardButton(f"{EMOJI['audio']} MP3", callback_data="quality_audio"),
        types.InlineKeyboardButton(f"{EMOJI['best']} BEST", callback_data="quality_best"),
        types.InlineKeyboardButton(f"{EMOJI['error']} CANCEL", callback_data="cancel")
    )
    return keyboard

def create_stats_message(user_id):
    return f"""
{EMOJI['stats']} <b>FTGAMER STATISTICS</b>
├ Total Downloads: <code>{download_stats['total']}</code>
├ Total Data: <code>{download_stats['size_gb']:.2f} GB</code>
└ Your ID: <code>{user_id}</code>
"""

# ========== DOWNLOAD ENGINE ==========
class DownloadManager:
    def start_download(self, url, quality, chat_id, message_id):
        thread = threading.Thread(target=self._download_process, args=(url, quality, chat_id, message_id))
        thread.start()
    
    def _download_process(self, url, quality, chat_id, message_id):
        try:
            download_stats['total'] += 1
            config = QUALITY_CONFIG.get(quality, QUALITY_CONFIG['best'])
            
            # Initialization
            init_msg = bot.send_message(chat_id, f"{get_spinner(0)} <b>Initializing Download...</b>", parse_mode="HTML")
            
            # Get info
            info = self._get_video_info(url)
            if not info: raise Exception("Could not fetch video information")
            
            # Download
            file_path = self._download_with_progress(url, quality, chat_id, init_msg.message_id, info)
            if not file_path: raise Exception("Download failed")
            
            # Send file
            file_size = os.path.getsize(file_path)
            download_stats['size_gb'] += file_size / (1024**3)
            self._send_file(chat_id, file_path, info, quality, file_size)
            
            bot.delete_message(chat_id, init_msg.message_id)
            self._cleanup(file_path)
        except Exception as e:
            logger.error(f"Error: {e}")
            bot.send_message(chat_id, f"❌ <b>Error:</b> {str(e)[:100]}", parse_mode="HTML")

    def _get_video_info(self, url):
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            return ydl.extract_info(url, download=False)

    def _download_with_progress(self, url, quality, chat_id, msg_id, info):
        temp_dir = tempfile.mkdtemp()
        output = os.path.join(temp_dir, '%(title).50s.%(ext)s')
        opts = {
            'format': QUALITY_CONFIG[quality]['format'],
            'outtmpl': output,
            'progress_hooks': [lambda d: self._progress_hook(d, chat_id, msg_id, info)],
            'quiet': True
        }
        if quality == 'audio':
            opts.update({'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}]})
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            res = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(res)
            if quality == 'audio': path = path.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            return path

    def _progress_hook(self, d, chat_id, msg_id, info):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%','')
                bar = create_progress_bar(float(p))
                text = f"<b>📥 Downloading...</b>\n\n{bar} <code>{p}%</code>\n⚡ <b>Speed:</b> {d.get('_speed_str','N/A')}"
                bot.edit_message_text(text, chat_id, msg_id, parse_mode="HTML")
            except: pass

    def _send_file(self, chat_id, path, info, quality, size):
        caption = f"🎬 <b>{info.get('title','Video')}</b>\n📦 Size: {format_size(size)}\n💎 Quality: {quality.upper()}"
        with open(path, 'rb') as f:
            if path.endswith('.mp3'): bot.send_audio(chat_id, f, caption=caption, parse_mode="HTML")
            else: bot.send_video(chat_id, f, caption=caption, supports_streaming=True, parse_mode="HTML")

    def _cleanup(self, path):
        try: shutil.rmtree(os.path.dirname(path))
        except: pass

dm = DownloadManager()

# ========== FIXED HANDLERS (THE FIX) ==========

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """FIX: Handle /start in a background thread to prevent Webhook looping"""
    # Start the logic in background
    threading.Thread(target=start_animation_logic, args=(message,)).start()
    # Return immediately to stop Telegram from retrying
    return "OK", 200

def start_animation_logic(message):
    """The actual animated logic moved here"""
    try:
        user_id = message.from_user.id
        msg = bot.send_message(message.chat.id, f"{get_spinner(0)} <b>Starting...</b>", parse_mode="HTML")
        
        # Short animation
        for i in range(1, 4):
            time.sleep(0.3)
            bot.edit_message_text(
                f"{get_spinner(i)} <b>Loading Premium Features {'.' * i}</b>",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode="HTML"
            )
        
        bot.edit_message_text(create_welcome_message(user_id), chat_id=message.chat.id, message_id=msg.message_id, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Start logic error: {e}")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    url = re.search(r'(https?://[^\s]+)', message.text)
    if url:
        user_sessions[message.chat.id] = {'url': url.group(0)}
        bot.send_message(message.chat.id, "<b>✅ Link Detected!</b>\nSelect quality below:", 
                         reply_markup=create_quality_keyboard(), parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "👋 <b>Send me a video link to download!</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    bot.answer_callback_query(call.id)
    if call.data.startswith('quality_'):
        url = user_sessions.get(call.message.chat.id, {}).get('url')
        if url: dm.start_download(url, call.data.split('_')[1], call.message.chat.id, call.message.message_id)
    elif call.data == 'cancel':
        bot.edit_message_text("❌ Cancelled.", call.message.chat.id, call.message.message_id)

# ========== FLASK WEBHOOK SETUP ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK'
    return 'Bad Request', 400

@app.route('/')
def home():
    return f"Bot is Online. Total Downloads: {download_stats['total']}"

if __name__ == '__main__':
    # Start Flask in a background thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=PORT), daemon=True).start()
    
    # Set Webhook (Update this with your ACTUAL URL from Koyeb)
    time.sleep(2)
    WEBHOOK_URL = "https://impossible-philippe-ftgamerv2-477c9a71.koyeb.app/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"🚀 Bot Started! Webhook set to: {WEBHOOK_URL}")
    
    while True:
        time.sleep(1)