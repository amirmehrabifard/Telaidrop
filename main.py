
import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from web3 import Web3

BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
CHAIN_RPC = os.getenv("CHAIN_RPC")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
CHANNEL_USERNAME = "@benjaminfranklintoken"

# اتصال به BSC
w3 = Web3(Web3.HTTPProvider(CHAIN_RPC))
contract_abi = [{
    "constant": False,
    "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
    "name": "transfer",
    "outputs": [{"name": "", "type": "bool"}],
    "type": "function"
}]
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=contract_abi)

# دیتابیس
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, wallet TEXT, invited_by INTEGER, rewarded INTEGER DEFAULT 0)")
conn.commit()

# پیام‌ها
MESSAGES = {
    "start": {
        "en": "Please join our channel first and then press /start.",
        "fa": "لطفاً ابتدا در کانال عضو شوید و سپس /start را بزنید."
    },
    "enter_wallet": {
        "en": "Please enter your BSC wallet address:",
        "fa": "لطفاً آدرس کیف پول BSC خود را وارد کنید:"
    },
    "invalid_wallet": {
        "en": "Invalid wallet address.",
        "fa": "آدرس کیف پول معتبر نیست."
    },
    "already_registered": {
        "en": "You have already registered.",
        "fa": "شما قبلاً ثبت‌نام کرده‌اید."
    },
    "reward_sent": {
        "en": "500 BJF tokens have been sent to your wallet.",
        "fa": "۵۰۰ توکن BJF به کیف پول شما ارسال شد."
    },
    "ref_reward": {
        "en": "Your referrer received 100 BJF tokens.",
        "fa": "معرف شما ۱۰۰ توکن BJF دریافت کرد."
    }
}

def get_lang(update: Update):
    code = update.effective_user.language_code or "en"
    return code if code in MESSAGES["start"] else "en"

async def check_membership(app, user_id):
    try:
        member = await app.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def send_tokens(to, amount):
    nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(WALLET_ADDRESS))
    tx = contract.functions.transfer(Web3.to_checksum_address(to), amount).build_transaction({
        'chainId': 56,
        'gas': 200000,
        'gasPrice': w3.to_wei('5', 'gwei'),
        'nonce': nonce,
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    return w3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    lang = get_lang(update)

    if not await check_membership(context.application, user_id):
        await update.message.reply_text(MESSAGES["start"][lang])
        return

    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        invited_by = int(args[0]) if args else None
        c.execute("INSERT INTO users (user_id, invited_by) VALUES (?, ?)", (user_id, invited_by))
        conn.commit()

    c.execute("SELECT wallet FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row and not row[0]:
        await update.message.reply_text(MESSAGES["enter_wallet"][lang])
    else:
        ref_link = f"https://t.me/benjaminfranklintoken_bot?start={user_id}"
        await update.message.reply_text(f"{MESSAGES['already_registered'][lang]}

Referral link: {ref_link}")

async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_lang(update)
    text = update.message.text.strip()

    if not w3.is_address(text):
        await update.message.reply_text(MESSAGES["invalid_wallet"][lang])
        return

    c.execute("SELECT rewarded FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        await update.message.reply_text("Please use /start first.")
        return

    rewarded = row[0]
    c.execute("UPDATE users SET wallet = ? WHERE user_id = ?", (text, user_id))
    conn.commit()

    if rewarded == 0:
        try:
            send_tokens(text, 500 * 10**18)
            c.execute("UPDATE users SET rewarded = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            await update.message.reply_text(MESSAGES["reward_sent"][lang])
        except Exception as e:
            await update.message.reply_text(f"Token send error: {e}")
            return

        c.execute("SELECT invited_by FROM users WHERE user_id = ?", (user_id,))
        inviter = c.fetchone()
        if inviter and inviter[0]:
            c.execute("SELECT wallet FROM users WHERE user_id = ?", (inviter[0],))
            inviter_wallet = c.fetchone()
            if inviter_wallet and inviter_wallet[0]:
                try:
                    send_tokens(inviter_wallet[0], 100 * 10**18)
                    await update.message.reply_text(MESSAGES["ref_reward"][lang])
                except:
                    pass

    ref_link = f"https://t.me/benjaminfranklintoken_bot?start={user_id}"
    await update.message.reply_text(f"Referral link: {ref_link}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet))
    app.run_polling()
