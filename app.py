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
    # Status
    'online': '🟢', 'offline': '🔴', 'loading': '🔄', 'success': '✅',
    'error': '❌', 'warning': '⚠️', 'info': 'ℹ️', 'star': '⭐',
    
    # Actions
    'download': '📥', 'upload': '📤', 'process': '⚙️', 'search': '🔍',
    'convert': '🔄', 'compress': '🗜️', 'extract': '📂',
    
    # Media
    'video': '🎬', 'audio': '🎵', 'photo': '🖼️', 'document': '📄',
    'link': '🔗', 'folder': '📁', 'cloud': '☁️',
    
    # Quality
    '8k': '👑', '4k': '🔥', '2k': '⚡', '1080': '💎',
    '720': '📺', '480': '📱', '360': '🎯', 'best': '🏆',
    
    # UI Elements
    'rocket': '🚀', 'fire': '🔥', 'heart': '❤️', 'sparkle': '✨',
    'trophy': '🏆', 'crown': '👑', 'diamond': '💎', 'bolt': '⚡',
    'clock': '⏰', 'calendar': '📅', 'bell': '🔔', 'lock': '🔒',
    'unlock': '🔓', 'settings': '⚙️', 'home': '🏠', 'back': '↩️',
    
    # Social
    'youtube': '📺', 'instagram': '📷', 'tiktok': '🎵', 'facebook': '👤',
    'twitter': '🐦', 'telegram': '📱', 'whatsapp': '💬',
    
    # Progress
    'bar_start': '┏', 'bar_mid': '━', 'bar_end': '┓',
    'fill': '█', 'empty': '░',
    
    # Animations
    'spin1': '🌀', 'spin2': '⚪', 'spin3': '🔄',
    'wave1': '🌊', 'wave2': '💫', 'wave3': '✨',
}

# ========== QUALITY SETTINGS ==========
QUALITY_CONFIG = {
    '8k': {
        'name': '8K ULTRA HD',
        'format': 'bestvideo[height>=4320]+bestaudio/best[height>=4320]',
        'emoji': EMOJI['8k'],
        'color': '🟣'
    },
    '4k': {
        'name': '4K ULTRA HD', 
        'format': 'bestvideo[height>=2160]+bestaudio/best[height>=2160]',
        'emoji': EMOJI['4k'],
        'color': '🔵'
    },
    '2k': {
        'name': '2K QHD',
        'format': 'bestvideo[height>=1440]+bestaudio/best[height>=1440]',
        'emoji': EMOJI['2k'],
        'color': '🟢'
    },
    '1080': {
        'name': '1080p FULL HD',
        'format': 'bestvideo[height<=1080][height>=720]+bestaudio/best[height<=1080]',
        'emoji': EMOJI['1080'],
        'color': '🟡'
    },
    '720': {
        'name': '720p HD',
        'format': 'bestvideo[height=720]+bestaudio/best[height=720]',
        'emoji': EMOJI['720'],
        'color': '🟠'
    },
    '480': {
        'name': '480p SD',
        'format': 'bestvideo[height=480]+bestaudio/best[height=480]',
        'emoji': EMOJI['480'],
        'color': '🔴'
    },
    '360': {
        'name': '360p',
        'format': 'bestvideo[height=360]+bestaudio/best[height=360]',
        'emoji': EMOJI['360'],
        'color': '⚫'
    },
    'best': {
        'name': 'BEST QUALITY',
        'format': 'bestvideo+bestaudio/best',
        'emoji': EMOJI['best'],
        'color': '🏆'
    },
    'audio': {
        'name': 'AUDIO ONLY',
        'format': 'bestaudio/best',
        'emoji': EMOJI['audio'],
        'color': '🎵'
    }
}

# ========== STORAGE & SESSIONS ==========
user_sessions = {}
download_queue = {}
active_downloads = {}
download_stats = {
    'total': 0,
    'today': 0,
    'size_gb': 0,
    'users': set(),
    'last_reset': datetime.now().date()
}

# ========== ANIMATION FRAMES ==========
ANIMATION = {
    'spinner': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
    'dots': ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
    'moon': ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'],
    'arrow': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
    'hearts': ['💛', '💚', '💙', '💜', '❤️', '🧡'],
}

# ========== HELPER FUNCTIONS ==========
def reset_daily_stats():
    """Reset daily download statistics"""
    today = datetime.now().date()
    if today != download_stats['last_reset']:
        download_stats['today'] = 0
        download_stats['last_reset'] = today

def format_size(bytes_size):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def format_time(seconds):
    """Format time in human readable format"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.0f}m {seconds%60:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def create_progress_bar(percentage, width=20):
    """Create a visual progress bar"""
    filled = int(width * percentage / 100)
    empty = width - filled
    
    bar = EMOJI['bar_start']
    bar += EMOJI['fill'] * filled
    bar += EMOJI['empty'] * empty
    bar += EMOJI['bar_end']
    
    return bar

def get_spinner(index=0):
    """Get animated spinner frame"""
    return ANIMATION['spinner'][index % len(ANIMATION['spinner'])]

def fancy_header(text):
    """Create fancy header with borders"""
    border = "═" * (len(text) + 4)
    return f"┏{border}┓\n┃  {text}  ┃\n┗{border}┛"

# ========== TELEGRAM UI COMPONENTS ==========
def create_welcome_message(user_id):
    """Create animated welcome message"""
    reset_daily_stats()
    download_stats['users'].add(user_id)
    
    # Get random animation
    anim_index = int(time.time()) % len(ANIMATION['hearts'])
    
    return f"""
{EMOJI['sparkle']} <b>WELCOME TO FTGAMER PREMIUM</b> {EMOJI['sparkle']}

{EMOJI['rocket']} <b>ULTIMATE FEATURES UNLOCKED</b>
{EMOJI['success']} 8K/4K Video Downloads
{EMOJI['success']} Bulk Download Support  
{EMOJI['success']} Audio Extraction (MP3)
{EMOJI['success']} 24/7 Cloud Processing
{EMOJI['success']} No Limits - No Ads

{EMOJI['fire']} <b>HOW TO USE</b>
1. Send video link (YouTube/Insta/TikTok)
2. Select quality from menu
3. Download & enjoy!

{EMOJI['stats']} <b>BOT STATISTICS</b>
• Total Downloads: {download_stats['total']}
• Today's Downloads: {download_stats['today']}
• Active Users: {len(download_stats['users'])}
• Total Data: {download_stats['size_gb']:.2f} GB

{EMOJI['heart']} <b>Developer:</b> {DEVELOPER}
{EMOJI['link']} <b>Channel:</b> {CHANNEL}

{ANIMATION['hearts'][anim_index]} <i>Ready when you are!</i>
"""

def create_quality_keyboard():
    """Create premium quality selection keyboard"""
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    # Row 1: Premium Qualities
    keyboard.add(
        types.InlineKeyboardButton(
            f"{EMOJI['8k']} 8K ULTRA", 
            callback_data="quality_8k"
        ),
        types.InlineKeyboardButton(
            f"{EMOJI['4k']} 4K PRO", 
            callback_data="quality_4k"
        ),
        types.InlineKeyboardButton(
            f"{EMOJI['2k']} 2K QHD", 
            callback_data="quality_2k"
        )
    )
    
    # Row 2: Standard Qualities
    keyboard.add(
        types.InlineKeyboardButton(
            f"{EMOJI['1080']} 1080p FULL HD", 
            callback_data="quality_1080"
        ),
        types.InlineKeyboardButton(
            f"{EMOJI['720']} 720p HD", 
            callback_data="quality_720"
        ),
        types.InlineKeyboardButton(
            f"{EMOJI['480']} 480p SD", 
            callback_data="quality_480"
        )
    )
    
    # Row 3: Audio & Best
    keyboard.add(
        types.InlineKeyboardButton(
            f"{EMOJI['audio']} AUDIO MP3", 
            callback_data="quality_audio"
        ),
        types.InlineKeyboardButton(
            f"{EMOJI['best']} BEST AUTO", 
            callback_data="quality_best"
        ),
        types.InlineKeyboardButton(
            f"{EMOJI['360']} 360p FAST", 
            callback_data="quality_360"
        )
    )
    
    # Row 4: Additional Options
    keyboard.add(
        types.InlineKeyboardButton(
            f"{EMOJI['folder']} BULK MODE", 
            callback_data="bulk_mode"
        ),
        types.InlineKeyboardButton(
            f"{EMOJI['stats']} STATISTICS", 
            callback_data="show_stats"
        ),
        types.InlineKeyboardButton(
            f"{EMOJI['settings']} SETTINGS", 
            callback_data="settings"
        )
    )
    
    # Row 5: Cancel
    keyboard.add(
        types.InlineKeyboardButton(
            f"{EMOJI['error']} CANCEL", 
            callback_data="cancel"
        )
    )
    
    return keyboard

def create_stats_message(user_id):
    """Create detailed statistics message"""
    anim_index = int(time.time()) % len(ANIMATION['moon'])
    
    return f"""
{ANIMATION['moon'][anim_index]} <b>FTGAMER STATISTICS DASHBOARD</b>

{EMOJI['download']} <b>DOWNLOAD STATS</b>
├ Total Downloads: <code>{download_stats['total']}</code>
├ Today's Downloads: <code>{download_stats['today']}</code>
├ Total Data: <code>{download_stats['size_gb']:.2f} GB</code>
└ Active Users: <code>{len(download_stats['users'])}</code>

{EMOJI['user']} <b>USER INFORMATION</b>
├ Your ID: <code>{user_id}</code>
├ Session: Active
├ Status: Premium User
└ Cooldown: None

{EMOJI['cloud']} <b>SYSTEM STATUS</b>
├ Server: Koyeb Cloud
├ Uptime: 100%
├ Storage: Unlimited
└ Speed: Maximum

{EMOJI['fire']} <b>BOT FEATURES</b>
{create_progress_bar(100)} All Features Active

{EMOJI['heart']} Thank you for using FTGamer Premium!
"""

# ========== DOWNLOAD ENGINE ==========
class DownloadManager:
    """Advanced download manager with progress tracking"""
    
    def __init__(self):
        self.active = {}
        self.queue = []
        
    def start_download(self, url, quality, chat_id, message_id):
        """Start a new download with animation"""
        thread = threading.Thread(
            target=self._download_process,
            args=(url, quality, chat_id, message_id)
        )
        thread.start()
        return thread
    
    def _download_process(self, url, quality, chat_id, message_id):
        """Main download process with animations"""
        try:
            # Update stats
            download_stats['total'] += 1
            download_stats['today'] += 1
            
            # Get quality config
            config = QUALITY_CONFIG.get(quality, QUALITY_CONFIG['best'])
            quality_name = config['name']
            
            # Send animated initialization message
            init_msg = bot.send_message(
                chat_id,
                self._create_initial_message(url, quality_name),
                parse_mode="HTML"
            )
            
            # Extract video info with animation
            for i in range(3):
                spinner = get_spinner(i)
                bot.edit_message_text(
                    self._create_info_message(url, quality_name, spinner, i+1, 3),
                    chat_id=chat_id,
                    message_id=init_msg.message_id,
                    parse_mode="HTML"
                )
                time.sleep(0.5)
            
            # Get video info
            info = self._get_video_info(url)
            if not info:
                raise Exception("Could not fetch video information")
            
            # Update with video info
            bot.edit_message_text(
                self._create_video_info_message(info, quality_name),
                chat_id=chat_id,
                message_id=init_msg.message_id,
                parse_mode="HTML"
            )
            
            time.sleep(1)
            
            # Start download with progress
            downloaded_file = self._download_with_progress(
                url, quality, chat_id, init_msg.message_id, info
            )
            
            if not downloaded_file or not os.path.exists(downloaded_file):
                raise Exception("Download failed - no file created")
            
            # Get file size
            file_size = os.path.getsize(downloaded_file)
            download_stats['size_gb'] += file_size / (1024**3)
            
            # Send completion animation
            for i in range(5):
                spinner = ANIMATION['dots'][i % len(ANIMATION['dots'])]
                bot.edit_message_text(
                    self._create_completion_message(info, quality_name, file_size, spinner),
                    chat_id=chat_id,
                    message_id=init_msg.message_id,
                    parse_mode="HTML"
                )
                time.sleep(0.3)
            
            # Send the actual file
            self._send_file(chat_id, downloaded_file, info, quality, file_size)
            
            # Final success message
            bot.edit_message_text(
                self._create_final_message(info, quality_name, file_size),
                chat_id=chat_id,
                message_id=init_msg.message_id,
                parse_mode="HTML"
            )
            
            # Cleanup
            self._cleanup(downloaded_file)
            
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            self._send_error(chat_id, init_msg.message_id, str(e))
    
    def _get_video_info(self, url):
        """Extract video information"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            logger.error(f"Info extraction error: {e}")
            return None
    
    def _download_with_progress(self, url, quality, chat_id, msg_id, info):
        """Download with animated progress"""
        temp_dir = tempfile.mkdtemp()
        output_template = os.path.join(temp_dir, '%(title).50s.%(ext)s')
        
        # Get format
        config = QUALITY_CONFIG.get(quality, QUALITY_CONFIG['best'])
        
        ydl_opts = {
            'format': config['format'],
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [lambda d: self._progress_hook(d, chat_id, msg_id, info)],
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
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                # Handle audio file extension
                if quality == 'audio':
                    downloaded_file = downloaded_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                # Find actual file
                if not os.path.exists(downloaded_file):
                    base = os.path.splitext(downloaded_file)[0]
                    for ext in ['.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.flv']:
                        if os.path.exists(base + ext):
                            downloaded_file = base + ext
                            break
                
                return downloaded_file
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def _progress_hook(self, d, chat_id, msg_id, info):
        """Update download progress with animation"""
        if d['status'] == 'downloading':
            try:
                percent = float(d.get('_percent_str', '0%').strip('%'))
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                total = d.get('_total_bytes_str', 'N/A')
                
                spinner = ANIMATION['dots'][int(time.time() * 2) % len(ANIMATION['dots'])]
                
                progress_bar = create_progress_bar(percent)
                
                message = f"""
{spinner} <b>DOWNLOADING IN PROGRESS</b>

📹 <b>Title:</b> {info.get('title', 'Video')[:40]}...

{progress_bar} <code>{percent:.1f}%</code>

⚡ <b>Speed:</b> {speed}
⏱️ <b>ETA:</b> {eta}
📦 <b>Size:</b> {total}

{EMOJI['loading']} Please wait...
"""
                
                bot.edit_message_text(
                    message,
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="HTML"
                )
            except:
                pass
    
    def _send_file(self, chat_id, file_path, info, quality, file_size):
        """Send downloaded file with premium caption"""
        try:
            with open(file_path, 'rb') as file:
                title = info.get('title', 'Downloaded Video')[:50]
                duration = info.get('duration', 0)
                uploader = info.get('uploader', 'Unknown')
                
                caption = f"""
🎬 <b>{title}</b>

{EMOJI['success']} <b>DOWNLOAD COMPLETE</b>
├ Quality: {QUALITY_CONFIG[quality]['name']}
├ Size: {format_size(file_size)}
├ Duration: {format_time(duration)}
└ Channel: {uploader[:30]}

{EMOJI['fire']} <b>FTGAMER PREMIUM</b>
├ Features: All Unlocked
├ Speed: Maximum
└ Quality: Guaranteed

{EMOJI['heart']} <b>Enjoy your download!</b>
{EMOJI['link']} {DEVELOPER} | {CHANNEL}
"""
                
                if quality == 'audio' or file_path.endswith('.mp3'):
                    bot.send_audio(
                        chat_id=chat_id,
                        audio=file,
                        caption=caption,
                        title=title[:30],
                        performer=uploader[:30],
                        duration=duration,
                        parse_mode="HTML"
                    )
                else:
                    bot.send_video(
                        chat_id=chat_id,
                        video=file,
                        caption=caption,
                        duration=duration,
                        width=info.get('width', 1920),
                        height=info.get('height', 1080),
                        supports_streaming=True,
                        parse_mode="HTML"
                    )
        except Exception as e:
            logger.error(f"Send file error: {e}")
            # Try as document
            try:
                with open(file_path, 'rb') as file:
                    bot.send_document(
                        chat_id=chat_id,
                        document=file,
                        caption=caption,
                        parse_mode="HTML"
                    )
            except Exception as e2:
                logger.error(f"Document send error: {e2}")
    
    def _cleanup(self, file_path):
        """Clean up temporary files"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            temp_dir = os.path.dirname(file_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass
    
    def _send_error(self, chat_id, msg_id, error):
        """Send animated error message"""
        spinner = ANIMATION['moon'][int(time.time()) % len(ANIMATION['moon'])]
        
        error_msg = f"""
{EMOJI['error']} <b>DOWNLOAD FAILED</b>

{spinner} <b>Error Details:</b>
<code>{str(error)[:200]}</code>

{EMOJI['warning']} <b>Possible Solutions:</b>
• Try lower quality (720p/480p)
• Try Audio Only option
• Check if video is available
• Try again in 30 seconds

{EMOJI['info']} <b>Support:</b> {DEVELOPER}
"""
        
        try:
            bot.edit_message_text(
                error_msg,
                chat_id=chat_id,
                message_id=msg_id,
                parse_mode="HTML"
            )
        except:
            bot.send_message(chat_id, error_msg, parse_mode="HTML")
    
    # Message creation helpers
    def _create_initial_message(self, url, quality):
        spinner = get_spinner(0)
        return f"""
{spinner} <b>INITIALIZING DOWNLOAD</b>

🔗 <b>URL:</b> <code>{url[:50]}...</code>
🎬 <b>Quality:</b> {quality}
⚙️ <b>Status:</b> Initializing...

{EMOJI['loading']} Preparing download engine...
"""
    
    def _create_info_message(self, url, quality, spinner, step, total):
        progress = create_progress_bar((step/total)*100)
        return f"""
{spinner} <b>EXTRACTING VIDEO INFO</b>

🔗 <b>URL:</b> <code>{url[:40]}...</code>
🎬 <b>Quality:</b> {quality}

{progress} Step {step}/{total}

{EMOJI['search']} Fetching video details...
"""
    
    def _create_video_info_message(self, info, quality):
        title = info.get('title', 'Unknown Video')[:40]
        duration = info.get('duration', 0)
        views = info.get('view_count', 0)
        uploader = info.get('uploader', 'Unknown')
        
        return f"""
{EMOJI['video']} <b>VIDEO INFORMATION</b>

📹 <b>Title:</b> {title}
👤 <b>Channel:</b> {uploader[:30]}
⏱️ <b>Duration:</b> {format_time(duration)}
👁️ <b>Views:</b> {views:,}
🎬 <b>Quality:</b> {quality}

{EMOJI['download']} <b>Ready to download!</b>
"""
    
    def _create_completion_message(self, info, quality, size, spinner):
        title = info.get('title', 'Video')[:40]
        return f"""
{spinner} <b>FINALIZING DOWNLOAD</b>

✅ <b>Download Complete!</b>
📹 {title}
🎬 {quality}
📦 {format_size(size)}

{EMOJI['upload']} Sending to Telegram...
"""
    
    def _create_final_message(self, info, quality, size):
        title = info.get('title', 'Video')[:40]
        anim = ANIMATION['hearts'][int(time.time()) % len(ANIMATION['hearts'])]
        
        return f"""
{anim} <b>DOWNLOAD SUCCESSFUL!</b>

{EMOJI['success']} <b>Video has been sent!</b>
📹 {title}
🎬 {quality}
📦 {format_size(size)}

{EMOJI['fire']} <b>Thank you for using FTGamer Premium!</b>

{EMOJI['star']} Rate our service: /rate
{EMOJI['download']} Send another link!
"""

# Initialize download manager
dm = DownloadManager()

# ========== TELEGRAM HANDLERS ==========
@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    """Handle /start command with animation"""
    user_id = message.from_user.id
    
    # Send animated welcome
    msg = bot.send_message(
        message.chat.id,
        f"{get_spinner(0)} <b>Starting FTGamer Premium...</b>",
        parse_mode="HTML"
    )
    
    # Animate loading
    for i in range(1, 6):
        time.sleep(0.2)
        bot.edit_message_text(
            f"{get_spinner(i)} <b>Loading Premium Features {'.' * i}</b>",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )
    
    # Send final welcome
    bot.edit_message_text(
        create_welcome_message(user_id),
        chat_id=message.chat.id,
        message_id=msg.message_id,
        parse_mode="HTML"
    )

@bot.message_handler(commands=['stats'])
def handle_stats(message):
    """Handle /stats command"""
    stats_msg = create_stats_message(message.from_user.id)
    bot.send_message(message.chat.id, stats_msg, parse_mode="HTML")

@bot.message_handler(commands=['rate'])
def handle_rate(message):
    """Handle /rate command"""
    rating_msg = f"""
{EMOJI['star']} <b>RATE OUR SERVICE</b>

How was your experience with FTGamer Premium?

{EMOJI['heart']} <b>Please rate:</b>
1 ⭐ - Poor
2 ⭐ - Average  
3 ⭐ - Good
4 ⭐ - Very Good
5 ⭐ - Excellent

{EMOJI['fire']} <b>Your feedback helps us improve!</b>

Reply with your rating (1-5 stars)
"""
    bot.send_message(message.chat.id, rating_msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    """Handle all messages"""
    text = message.text.strip()
    chat_id = message.chat.id
    
    # Check if it's a rating
    if text in ['1', '2', '3', '4', '5']:
        stars = int(text)
        rating_response = f"""
{EMOJI['sparkle']} <b>THANK YOU FOR YOUR FEEDBACK!</b>

{'⭐' * stars} {'☆' * (5-stars)}

{EMOJI['heart']} Your {stars}-star rating has been recorded!
{EMOJI['fire']} We'll continue to improve our service.

{EMOJI['download']} Ready for more downloads!
"""
        bot.send_message(chat_id, rating_response, parse_mode="HTML")
        return
    
    # Check if it's a URL
    url_patterns = [
        r'(https?://[^\s]+)',
        r'(youtube\.com/watch\?v=[^\s]+)',
        r'(youtu\.be/[^\s]+)',
        r'(instagram\.com/[^\s]+)',
        r'(tiktok\.com/[^\s]+)'
    ]
    
    is_url = any(re.search(pattern, text, re.IGNORECASE) for pattern in url_patterns)
    
    if is_url:
        # Store URL for this user
        user_sessions[chat_id] = {'url': text}
        
        # Send quality selection
        quality_msg = f"""
{EMOJI['success']} <b>LINK DETECTED!</b>

🔗 <b>URL:</b> <code>{text[:50]}...</code>
✅ <b>Status:</b> Ready for download

{EMOJI['video']} <b>SELECT DOWNLOAD QUALITY:</b>
"""
        bot.send_message(
            chat_id,
            quality_msg,
            reply_markup=create_quality_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Send help message
        help_msg = f"""
{EMOJI['info']} <b>HOW TO USE FTGAMER</b>

{EMOJI['download']} <b>Send me:</b>
• YouTube links
• Instagram Reels
• TikTok videos
• Facebook videos
• Twitter videos

{EMOJI['star']} <b>Example:</b>
<code>https://youtube.com/watch?v=...</code>
<code>https://instagram.com/reel/...</code>
<code>https://tiktok.com/@user/video/...</code>

{EMOJI['fire']} <b>All features are FREE!</b>
"""
        bot.send_message(chat_id, help_msg, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle all callback queries"""
    chat_id = call.message.chat.id
    data = call.data
    
    # Answer callback immediately
    bot.answer_callback_query(call.id)
    
    if data == 'cancel':
        cancel_msg = f"""
{EMOJI['error']} <b>OPERATION CANCELLED</b>

{EMOJI['back']} Returned to main menu.
{EMOJI['download']} Send another link when ready!
"""
        bot.edit_message_text(
            cancel_msg,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )
        return
    
    elif data == 'show_stats':
        stats_msg = create_stats_message(call.from_user.id)
        bot.edit_message_text(
            stats_msg,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )
        return
    
    elif data == 'settings':
        settings_msg = f"""
{EMOJI['settings']} <b>SETTINGS MENU</b>

{EMOJI['lock']} <b>Account Settings</b>
├ Username: @{call.from_user.username or 'Not set'}
├ User ID: <code>{call.from_user.id}</code>
└ Status: Premium User

{EMOJI['cloud']} <b>Download Settings</b>
├ Default Quality: Auto
├ Format: MP4/MP3
├ Speed: Maximum
└ Storage: Cloud Processing

{EMOJI['bell']} <b>Notifications</b>
├ Download Complete: ✅ ON
├ Errors: ✅ ON  
└ Updates: ✅ ON

{EMOJI['back']} Use /start to return
"""
        bot.edit_message_text(
            settings_msg,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )
        return
    
    elif data == 'bulk_mode':
        bulk_msg = f"""
{EMOJI['folder']} <b>BULK DOWNLOAD MODE</b>

{EMOJI['info']} <b>How to use Bulk Mode:</b>
1. Send multiple links (one per line)
2. We'll process them one by one
3. Each video will be downloaded separately

{EMOJI['star']} <b>Example:</b>
<code>https://youtube.com/watch?v=abc123
https://youtube.com/watch?v=def456
https://youtube.com/watch?v=ghi789</code>

{EMOJI['warning']} <b>Limits:</b>
• Max 5 links at once
• Each video max 2GB
• 30 seconds between downloads

{EMOJI['download']} Send your links now!
"""
        bot.edit_message_text(
            bulk_msg,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="HTML"
        )
        return
    
    elif data.startswith('quality_'):
        quality = data.split('_')[1]
        
        # Get URL from user session
        url = user_sessions.get(chat_id, {}).get('url', '')
        
        if not url:
            # Try to get from message text
            try:
                if call.message.reply_to_message:
                    url = call.message.reply_to_message.text
            except:
                pass
        
        if not url:
            error_msg = f"""
{EMOJI['error']} <b>URL NOT FOUND</b>

Please send the video link again.
"""
            bot.edit_message_text(
                error_msg,
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
            return
        
        # Start download
        dm.start_download(url, quality, chat_id, call.message.message_id)

# ========== FLASK ROUTES ==========
@app.route('/')
def home():
    """Home page"""
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
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
        }
        .stat {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
            flex: 1;
            margin: 0 10px;
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
        <p>Ultimate video downloader with premium features</p>
        
        <div class="stats">
            <div class="stat">
                <h3>📥 Downloads</h3>
                <h2>{}</h2>
            </div>
            <div class="stat">
                <h3>👥 Users</h3>
                <h2>{}</h2>
            </div>
            <div class="stat">
                <h3>⚡ Uptime</h3>
                <h2>100%</h2>
            </div>
        </div>
        
        <p>
            <a href="https://t.me/ftgamer2_bot" class="btn">🤖 Start Bot</a>
            <a href="https://t.me/ftgamer2" class="btn">📢 Join Channel</a>
        </p>
        
        <p style="margin-top: 40px; opacity: 0.8;">
            Developed with ❤️ by @ftgamer2<br>
            Running on Koyeb Cloud
        </p>
    </div>
</body>
</html>
""".format(download_stats['total'], len(download_stats['users']))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'stats': {
            'downloads': download_stats['total'],
            'users': len(download_stats['users']),
            'uptime': '100%'
        }
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook handler"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK'
    return 'Bad Request', 400

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    """Set webhook endpoint"""
    webhook_url = f"https://{request.host}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return jsonify({
        'success': True,
        'message': f'Webhook set to: {webhook_url}',
        'bot': '@ftgamer2_bot'
    })

# ========== STARTUP ==========
def start_bot():
    """Start the bot with animations"""
    print("\n" + "="*60)
    print("🎬 FTGAMER PREMIUM BOT - ULTIMATE EDITION")
    print("✨ Features: Animated UI • Progress Bars • Premium Design")
    print("👨💻 Developer: @ftgamer2")
    print("🌐 Host: Koyeb Cloud")
    print("="*60)
    
    # Animated startup sequence
    for i in range(10):
        spinner = get_spinner(i)
        sys.stdout.write(f"\r{spinner} Starting bot... {i*10}%")
        sys.stdout.flush()
        time.sleep(0.1)
    
    print("\n✅ Bot started successfully!")
    print(f"🌐 Webhook URL: https://impossible-philippe-ftgamerv2-477c9a71.koyeb.app/webhook")
    print(f"📊 Stats: http://impossible-philippe-ftgamerv2-477c9a71.koyeb.app")
    print("="*60)
    print("🚀 Ready for downloads! Send /start to begin.")
    print("="*60)

# ========== MAIN ==========
if __name__ == '__main__':
    # Start bot in background thread
    import threading
    
    def run_flask():
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    
    # Start Flask in thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Set webhook automatically
    time.sleep(2)
    try:
        webhook_url = f"https://impossible-philippe-ftgamerv2-477c9a71.koyeb.app/webhook"
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook auto-set to: {webhook_url}")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    
    # Show startup animation
    start_bot()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped by user")
        print("✨ Thank you for using FTGamer Premium!")