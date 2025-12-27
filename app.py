import os
import sys
import logging
import asyncio
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

# ========== KOYEB CONFIGURATION ==========
# Flask is REQUIRED for Koyeb to keep the service "Healthy"
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))

@app.route('/')
def health_check():
    return "Bot is Running!", 200

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# ========== BOT CONFIGURATION ==========
TOKEN = "8598243397:AAGvpqyAIhQuIIJEj4Y8cxvdseB9-0zeOEU" # Change this at @BotFather!
DEVELOPER = "@ftgamer2"
CHANNEL = "https://t.me/ftgamer2"

# Quality Settings
QUALITIES = {
    '1080': {'name': '1080p Full HD', 'format': 'bestvideo[height<=1080]+bestaudio/best'},
    '720': {'name': '720p HD', 'format': 'bestvideo[height<=720]+bestaudio/best'},
    '480': {'name': '480p SD', 'format': 'bestvideo[height<=480]+bestaudio/best'},
    'audio': {'name': 'MP3 Audio', 'format': 'bestaudio/best'}
}

# ========== BOT LOGIC ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = f"🚀 <b>FTGamer Premium Downloader</b>\n\nSend me a link from YouTube, Instagram, or Pinterest!\n\n👤 Dev: {DEVELOPER}"
    await update.message.reply_html(welcome)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    keyboard = [
        [InlineKeyboardButton("💎 1080p", callback_data=f"dl_1080_{url}"),
         InlineKeyboardButton("📺 720p", callback_data=f"dl_720_{url}")],
        [InlineKeyboardButton("📱 480p", callback_data=f"dl_480_{url}"),
         InlineKeyboardButton("🎵 MP3", callback_data=f"dl_audio_{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Link Detected! Select Quality:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # data format: dl_quality_url
    _, quality, url = query.data.split("_", 2)
    chat_id = query.message.chat_id
    
    status_msg = await query.edit_message_text(f"⏳ <b>Processing {quality}...</b>\nPlease wait, this may take a minute.", parse_mode="HTML")

    try:
        # YT-DLP OPTIONS (The "Anti-Bot" fix)
        ydl_opts = {
            'format': QUALITIES[quality]['format'],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
        }

        if quality == 'audio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if quality == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        # Send File
        await status_msg.edit_text("📤 <b>Uploading to Telegram...</b>", parse_mode="HTML")
        with open(filename, 'rb') as f:
            if quality == 'audio':
                await context.bot.send_audio(chat_id, f, caption=f"🎵 {info['title']}")
            else:
                await context.bot.send_video(chat_id, f, caption=f"🎬 {info['title']}", supports_streaming=True)
        
        await status_msg.delete()
        os.remove(filename) # Clean up space

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error:</b>\n<code>{str(e)[:100]}</code>", parse_mode="HTML")

# ========== MAIN RUNNER ==========

def main():
    # 1. Start Flask for Koyeb Health Check
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"✅ Health Check Server started on port {PORT}")

    # 2. Start Telegram Bot
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 Bot is Polling...")
    application.run_polling()

if __name__ == '__main__':
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    main()
