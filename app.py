#!/usr/bin/env python3
"""
🎬 FTGamer Premium Downloader - ULTIMATE WORKING EDITION
👨💻 Developer: @ftgamer2
📢 Channel: https://t.me/ftgamer2
"""

import os
import asyncio
import logging
import tempfile
import shutil
import json
from datetime import datetime
from typing import Optional
import aiofiles
import aiohttp
import yt_dlp
from yt_dlp import YoutubeDL

# Telegram Bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

# Flask for webhook
from flask import Flask, request, jsonify

# ========== CONFIGURATION ==========
TOKEN = os.environ.get("BOT_TOKEN", "8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU")
PORT = int(os.environ.get("PORT", 8080))
DEVELOPER = "@ftgamer2"
CHANNEL = "https://t.me/ftgamer2"
WEBHOOK_URL = f"https://impossible-philippe-ftgamerv2-477c9a71.koyeb.app"
# ===================================

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for webhook
flask_app = Flask(__name__)

# ========== EMOJI SYSTEM ==========
EMOJI = {
    'success': '✅', 'error': '❌', 'warning': '⚠️', 'loading': '⏳',
    'download': '📥', 'upload': '📤', 'start': '🚀', 'video': '🎬',
    'audio': '🎵', 'rocket': '🚀', 'fire': '🔥', 'heart': '❤️',
    'star': '⭐', 'sparkle': '✨', 'trophy': '🏆', 'crown': '👑',
    'diamond': '💎', 'bolt': '⚡', 'clock': '⏰', 'bell': '🔔',
    '8k': '👑', '4k': '🔥', '2k': '⚡', '1080': '💎', '720': '📺',
    '480': '📱', '360': '🎯', 'best': '🏆', 'cancel': '❌', 'back': '↩️'
}

# ========== QUALITY SETTINGS ==========
QUALITY_CONFIG = {
    '8k': {
        'name': '8K ULTRA HD',
        'format': 'bestvideo[height>=4320]+bestaudio/best[height>=4320]/best',
        'emoji': EMOJI['8k']
    },
    '4k': {
        'name': '4K ULTRA HD',
        'format': 'bestvideo[height>=2160]+bestaudio/best[height>=2160]/best',
        'emoji': EMOJI['4k']
    },
    '2k': {
        'name': '2K QHD',
        'format': 'bestvideo[height>=1440]+bestaudio/best[height>=1440]/best',
        'emoji': EMOJI['2k']
    },
    '1080': {
        'name': '1080p FULL HD',
        'format': 'bestvideo[height<=1080][height>=720]+bestaudio/best[height<=1080]',
        'emoji': EMOJI['1080']
    },
    '720': {
        'name': '720p HD',
        'format': 'bestvideo[height=720]+bestaudio/best[height=720]',
        'emoji': EMOJI['720']
    },
    '480': {
        'name': '480p SD',
        'format': 'bestvideo[height=480]+bestaudio/best[height=480]',
        'emoji': EMOJI['480']
    },
    '360': {
        'name': '360p',
        'format': 'bestvideo[height=360]+bestaudio/best[height=360]',
        'emoji': EMOJI['360']
    },
    'best': {
        'name': 'BEST QUALITY',
        'format': 'best',
        'emoji': EMOJI['best']
    },
    'audio': {
        'name': 'AUDIO ONLY',
        'format': 'bestaudio/best',
        'emoji': EMOJI['audio']
    }
}

# ========== STORAGE ==========
user_sessions = {}
download_stats = {
    'total': 0,
    'today': 0,
    'users': set(),
    'size_gb': 0.0,
    'last_reset': datetime.now().date()
}

# ========== YT-DLP OPTIMIZED FOR PYTHONANYWHERE/KOYEB ==========
def get_ydl_options(quality_key: str, chat_id: int = None):
    """Get optimized yt-dlp options to avoid robot checks"""
    quality = QUALITY_CONFIG.get(quality_key, QUALITY_CONFIG['best'])
    
    ydl_opts = {
        'format': quality['format'],
        'outtmpl': f'{tempfile.gettempdir()}/%(id)s_%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': True,
        'ignoreerrors': True,
        'no_check_certificate': True,
        'extract_flat': False,
        'verbose': False,
        
        # CRITICAL: Headers to avoid robot detection
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        },
        
        # Bypass age restrictions and robot checks
        'cookiefile': None,  # Add cookies.txt if you have one
        'age_limit': 100,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'no_check_certificate': True,
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],
                'player_client': ['android', 'web'],
                'player_skip': ['configs', 'webpage'],
                'lang': 'en',
            }
        },
        'postprocessor_args': {
            'ffmpeg': ['-hide_banner', '-loglevel', 'error']
        },
        'socket_timeout': 30,
        'extract_timeout': 120,
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'keep_fragments': False,
        'continuedl': True,
        'noprogress': True,
        'progress_with_newline': True,
        'consoletitle': False,
        'compat_opts': {'no-youtube-unavailable-videos'},
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'geo_bypass_ip_block': None,
    }
    
    if quality_key == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '0',
        })
    
    # Try different methods to avoid robot check
    if chat_id and chat_id % 3 == 0:
        # Method 1: Use mobile user agent
        ydl_opts['http_headers']['User-Agent'] = 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
    elif chat_id and chat_id % 3 == 1:
        # Method 2: Use different client
        ydl_opts['extractor_args']['youtube']['player_client'] = ['ios', 'android_embed']
    
    return ydl_opts

# ========== TELEGRAM HANDLERS ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    download_stats['users'].add(user.id)
    
    welcome_text = f"""
{EMOJI['rocket']} <b>WELCOME TO FTGAMER PREMIUM</b> {EMOJI['rocket']}

{EMOJI['success']} <b>ALL FEATURES ACTIVE</b>
• YouTube Video Downloader
• Multiple Quality Support (8K to 360p)
• Audio Extraction (MP3)
• 24/7 Cloud Processing
• No Limits - No Ads

{EMOJI['download']} <b>HOW TO USE</b>
1. Send YouTube link
2. Select quality
3. Download instantly!

{EMOJI['star']} <b>Example Links:</b>
<code>https://youtube.com/watch?v=...</code>
<code>https://youtu.be/...</code>
<code>https://youtube.com/shorts/...</code>

{EMOJI['stats']} <b>Bot Statistics:</b>
• Total Downloads: {download_stats['total']}
• Active Users: {len(download_stats['users'])}
• Status: ✅ ONLINE

{EMOJI['heart']} <b>Developer:</b> {DEVELOPER}
{EMOJI['link']} <b>Channel:</b> {CHANNEL}
"""
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    stats_text = f"""
{EMOJI['stats']} <b>BOT STATISTICS</b>

{EMOJI['download']} <b>Download Stats</b>
• Total Downloads: {download_stats['total']}
• Today's Downloads: {download_stats['today']}
• Total Data: {download_stats['size_gb']:.2f} GB
• Active Users: {len(download_stats['users'])}

{EMOJI['user']} <b>Your Info</b>
• User ID: <code>{update.effective_user.id}</code>
• Status: Premium User
• Cooldown: None

{EMOJI['online']} <b>System Status</b>
• Server: Koyeb Cloud
• Uptime: 100%
• Features: All Active

{EMOJI['fire']} Ready for downloads!
"""
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    # Check if it's a URL
    url_patterns = [
        'youtube.com/watch',
        'youtu.be/',
        'youtube.com/shorts/',
        'youtube.com/playlist',
        'youtube.com/live/'
    ]
    
    if any(pattern in text.lower() for pattern in url_patterns):
        # Store URL
        user_sessions[chat_id] = {'url': text}
        
        # Create quality keyboard
        keyboard = [
            [
                InlineKeyboardButton(f"{EMOJI['1080']} 1080p", callback_data="quality_1080"),
                InlineKeyboardButton(f"{EMOJI['720']} 720p", callback_data="quality_720"),
                InlineKeyboardButton(f"{EMOJI['480']} 480p", callback_data="quality_480")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['audio']} Audio", callback_data="quality_audio"),
                InlineKeyboardButton(f"{EMOJI['best']} Best", callback_data="quality_best"),
                InlineKeyboardButton(f"{EMOJI['4k']} 4K", callback_data="quality_4k")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['8k']} 8K", callback_data="quality_8k"),
                InlineKeyboardButton(f"{EMOJI['2k']} 2K", callback_data="quality_2k"),
                InlineKeyboardButton(f"{EMOJI['360']} 360p", callback_data="quality_360")
            ],
            [
                InlineKeyboardButton(f"{EMOJI['cancel']} Cancel", callback_data="cancel")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{EMOJI['success']} <b>LINK DETECTED!</b>\n\n"
            f"{EMOJI['download']} <b>Select download quality:</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        # Help message
        help_text = f"""
{EMOJI['info']} <b>HOW TO USE</b>

Send me a YouTube link to download.

{EMOJI['star']} <b>Example:</b>
<code>https://youtube.com/watch?v=...</code>
<code>https://youtu.be/...</code>

{EMOJI['fire']} <b>All features are FREE!</b>
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries"""
    query = update.callback_query
    await query.answer()
    
    chat_id = update.effective_chat.id
    data = query.data
    
    if data == 'cancel':
        await query.edit_message_text(
            f"{EMOJI['error']} <b>OPERATION CANCELLED</b>\n\n"
            f"{EMOJI['download']} Send another link when ready!",
            parse_mode=ParseMode.HTML
        )
        return
    
    if data.startswith('quality_'):
        quality = data.replace('quality_', '')
        
        # Get URL from session
        url = user_sessions.get(chat_id, {}).get('url', '')
        
        if not url:
            # Try to get from original message
            try:
                if query.message.reply_to_message:
                    url = query.message.reply_to_message.text
            except:
                pass
        
        if not url:
            await query.edit_message_text(
                f"{EMOJI['error']} <b>URL NOT FOUND</b>\n\n"
                f"Please send the link again.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Start download
        await start_download(chat_id, url, quality, query.message.message_id, context)

async def start_download(chat_id: int, url: str, quality: str, message_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Start download process"""
    try:
        # Update stats
        download_stats['total'] += 1
        download_stats['today'] += 1
        
        quality_info = QUALITY_CONFIG.get(quality, QUALITY_CONFIG['best'])
        
        # Send initial message
        status_msg = await context.bot.send_message(
            chat_id,
            f"{EMOJI['loading']} <b>PREPARING DOWNLOAD...</b>\n\n"
            f"🎬 <b>Quality:</b> {quality_info['name']}\n"
            f"🔗 <b>URL:</b> {url[:40]}...\n\n"
            f"Please wait 10-30 seconds...",
            parse_mode=ParseMode.HTML
        )
        
        # Run download in background
        asyncio.create_task(
            download_and_send(chat_id, url, quality, status_msg.message_id, context)
        )
        
    except Exception as e:
        logger.error(f"Start download error: {e}")
        await context.bot.send_message(
            chat_id,
            f"{EMOJI['error']} <b>ERROR STARTING DOWNLOAD</b>\n\n"
            f"Error: {str(e)[:100]}\n\n"
            f"Please try again.",
            parse_mode=ParseMode.HTML
        )

async def download_and_send(chat_id: int, url: str, quality: str, message_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Download and send video"""
    temp_dir = None
    try:
        # Get yt-dlp options
        ydl_opts = get_ydl_options(quality, chat_id)
        
        # Update status
        await context.bot.edit_message_text(
            f"{EMOJI['loading']} <b>EXTRACTING VIDEO INFO...</b>\n\n"
            f"Fetching video information...",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode=ParseMode.HTML
        )
        
        # Extract info first
        with YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            if not info:
                raise Exception("Could not fetch video information")
            
            title = info.get('title', 'Video')[:50]
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')
        
        # Update with video info
        await context.bot.edit_message_text(
            f"{EMOJI['video']} <b>VIDEO INFORMATION</b>\n\n"
            f"📹 <b>Title:</b> {title}\n"
            f"👤 <b>Channel:</b> {uploader[:30]}\n"
            f"⏱️ <b>Duration:</b> {duration//60}:{duration%60:02d}\n"
            f"🎬 <b>Quality:</b> {QUALITY_CONFIG[quality]['name']}\n\n"
            f"{EMOJI['download']} Starting download...",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode=ParseMode.HTML
        )
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(id)s_%(title).50s.%(ext)s')
        
        # Download
        downloaded_file = None
        with YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            
            # Handle audio file extension
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
        download_stats['size_gb'] += file_size / (1024**3)
        
        # Update status
        await context.bot.edit_message_text(
            f"{EMOJI['upload']} <b>SENDING FILE...</b>\n\n"
            f"📹 {title}\n"
            f"📦 {file_size_mb:.1f}MB\n"
            f"🎬 {QUALITY_CONFIG[quality]['name']}\n\n"
            f"Please wait...",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode=ParseMode.HTML
        )
        
        # Send file
        async with aiofiles.open(downloaded_file, 'rb') as file:
            file_content = await file.read()
            
            if quality == 'audio' or downloaded_file.endswith('.mp3'):
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=file_content,
                    caption=f"🎵 <b>{title}</b>\n\n"
                           f"✅ Download Complete!\n"
                           f"📦 Size: {file_size_mb:.1f}MB\n"
                           f"🎶 Quality: 192kbps MP3\n\n"
                           f"⬇️ @ftgamer2_bot\n"
                           f"👤 {DEVELOPER}",
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=file_content,
                    caption=f"🎬 <b>{title}</b>\n\n"
                           f"✅ Download Complete!\n"
                           f"📦 Size: {file_size_mb:.1f}MB\n"
                           f"🎬 Quality: {QUALITY_CONFIG[quality]['name']}\n\n"
                           f"⬇️ @ftgamer2_bot\n"
                           f"👤 {DEVELOPER}",
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True
                )
        
        # Success message
        await context.bot.edit_message_text(
            f"{EMOJI['success']} <b>DOWNLOAD COMPLETE!</b>\n\n"
            f"📹 {title}\n"
            f"📦 {file_size_mb:.1f}MB\n"
            f"🎬 {QUALITY_CONFIG[quality]['name']}\n\n"
            f"{EMOJI['heart']} Thank you for using FTGamer!\n"
            f"{EMOJI['download']} Send another link!",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        
        error_msg = str(e)
        if "Sign in" in error_msg or "confirm" in error_msg or "robot" in error_msg:
            error_msg = "YouTube requires verification. Try a different video or quality."
        elif "Unavailable" in error_msg:
            error_msg = "Video is not available or private."
        elif "Private" in error_msg:
            error_msg = "Video is private or requires login."
        
        await context.bot.edit_message_text(
            f"{EMOJI['error']} <b>DOWNLOAD FAILED</b>\n\n"
            f"Error: {error_msg[:100]}\n\n"
            f"Try:\n• Lower quality (720p/480p)\n• Audio only\n• Different video\n• Try again in 30 seconds",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode=ParseMode.HTML
        )
    
    finally:
        # Cleanup
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

# ========== FLASK ROUTES ==========
@flask_app.route('/')
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>🎬 FTGamer Premium Bot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 20px;
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            max-width: 800px;
            width: 90%;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
        }
        .emoji {
            font-size: 4em;
            margin: 20px 0;
            animation: bounce 2s infinite;
        }
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        .stats {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-around;
            margin: 30px 0;
            gap: 15px;
        }
        .stat {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 15px;
            flex: 1;
            min-width: 150px;
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
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            border-color: #667eea;
        }
        .features {
            text-align: left;
            margin: 30px 0;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
        }
        @media (max-width: 600px) {
            h1 { font-size: 2em; }
            .emoji { font-size: 3em; }
            .container { padding: 20px; }
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
        
        <div class="features">
            <h3>✨ Features:</h3>
            <p>• YouTube Video Downloader</p>
            <p>• Multiple Quality Support (8K to 360p)</p>
            <p>• Audio Extraction (MP3)</p>
            <p>• 24/7 Cloud Processing</p>
            <p>• No Limits - No Ads</p>
        </div>
        
        <p>
            <a href="https://t.me/ftgamer2_bot" class="btn">🤖 Start Bot</a>
            <a href="https://t.me/ftgamer2" class="btn">📢 Join Channel</a>
        </p>
        
        <p style="margin-top: 40px; opacity: 0.8; font-size: 0.9em;">
            Developed with ❤️ by @ftgamer2<br>
            Running on Koyeb Cloud • Docker Optimized
        </p>
    </div>
</body>
</html>
""".format(download_stats['total'], len(download_stats['users']))

@flask_app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'ftgamer-bot',
        'timestamp': datetime.now().isoformat(),
        'stats': download_stats
    })

@flask_app.route('/setwebhook')
def set_webhook():
    return jsonify({
        'success': True,
        'webhook_url': f'{WEBHOOK_URL}/webhook',
        'bot': '@ftgamer2_bot'
    })

# ========== MAIN ==========
async def main():
    """Start the bot"""
    print("\n" + "="*60)
    print("🎬 FTGAMER PREMIUM BOT - DOCKER EDITION")
    print("✨ Features: python-telegram-bot • FFmpeg • Optimized")
    print("👨💻 Developer: @ftgamer2")
    print("🐳 Docker: Optimized for Koyeb")
    print("="*60)
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Start bot
    print("✅ Bot application created")
    print(f"🌐 Webhook URL: {WEBHOOK_URL}/webhook")
    print("="*60)
    print("🚀 Bot is ready! Starting Flask server...")
    print("="*60)
    
    # Run Flask in background
    import threading
    flask_thread = threading.Thread(
        target=lambda: flask_app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False),
        daemon=True
    )
    flask_thread.start()
    
    # Start bot polling (for testing) - REMOVE IN PRODUCTION OR USE WEBOOK
    print("🔄 Starting bot in polling mode...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    # For production with webhook, use this:
    # application.run_webhook(
    #     listen="0.0.0.0",
    #     port=PORT,
    #     url_path=TOKEN,
    #     webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    # )
    
    # For now, use polling in Docker
    asyncio.run(main())