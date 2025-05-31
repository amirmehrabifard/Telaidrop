import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

PORT = int(os.environ.get("PORT", 10000))
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")  # به صورت عددی یا @channelusername

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# پیغام‌ها به دو زبان
MESSAGES = {
    'start': {
        'fa': "سلام! برای ادامه عضو کانال شوید.",
        'en': "Hello! Please join the channel to proceed."
    },
    'already_registered': {
        'fa': "شما قبلاً ثبت‌نام کرده‌اید. 🎉",
        'en': "You are already registered. 🎉"
    },
    'joined': {
        'fa': "✅ شما عضو کانال هستید.",
        'en': "✅ You are a channel member."
    },
    'not_joined': {
        'fa': "❌ برای استفاده از بات ابتدا باید عضو کانال شوید.",
        'en': "❌ Please join the channel first to use this bot."
    }
}

registered_users = {}

def get_lang(update: Update) -> str:
    lang = update.effective_user.language_code
    return 'fa' if lang == 'fa' else 'en'

async def check_membership(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"خطا در بررسی عضویت: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = get_lang(update)

    if not await check_membership(context.bot, user.id):
        await update.message.reply_text(MESSAGES['not_joined'][lang])
        return

    if user.id in registered_users:
        ref_link = f"https://t.me/{context.bot.username}?start={user.id}"
        await update.message.reply_text(
            "{}\n\nReferral link: {}".format(MESSAGES['already_registered'][lang], ref_link),
            parse_mode=ParseMode.HTML
        )
    else:
        registered_users[user.id] = True
        await update.message.reply_text(MESSAGES['joined'][lang])

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update)
    await update.message.reply_text(MESSAGES['start'][lang])

def run_webhook():
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running.')

    server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
    logger.info(f"Listening on port {PORT}...")
    server.serve_forever()

async def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    run_webhook()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
