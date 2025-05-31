
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 🔧 تنظیمات
TOKEN = os.getenv("BOT_TOKEN")  # ← از متغیر محیطی گرفته می‌شود
CHANNEL_ID = "@channelusername"
MESSAGES = {
    'already_registered': {
        'fa': 'شما قبلاً ثبت‌نام کرده‌اید.',
        'en': 'You have already registered.',
    },
}

# 🧠 هندلر شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = 'fa'

    chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
    if chat_member.status not in ['member', 'administrator', 'creator']:
        await update.message.reply_text("❗️لطفاً ابتدا در کانال عضو شوید و سپس /start را بزنید.")
        return

    if 'registered' in context.user_data:
        await update.message.reply_text(f"{MESSAGES['already_registered'][lang]}")
        return

    context.user_data['registered'] = True
    await update.message.reply_text("✅ ثبت‌نام شما با موفقیت انجام شد!")

# ⚙️ راه‌اندازی
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
