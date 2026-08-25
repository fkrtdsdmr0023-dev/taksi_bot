import os
import asyncio
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8922084774:AAGJRthYR1LH9O2ZhyE3JwBVzfsZ8jwzse4"
MERKEZ_ID = 8860608922

ALL_USERS = set()
LAST_STATUS = "Henüz Merkez bir bildirim paylaşmadı."
LAST_STATUS_TIME = ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    ALL_USERS.add(user_id)

    if user_id == MERKEZ_ID:
        keyboard = [
            ["🔴 DÖNÜŞLER MERKEZ"],
            ["🔵 DÖNÜŞLER AVM"],
            ["🟢 HERKES YERİNE"],
            ["🟡 HERKES YERİNE YENİ DURAK MERKEZE"],
            ["📊 AKTİF KİŞİ SAYISI"]
        ]
    else:
        keyboard = [
            ["⚡ 📢 SON DURUM 📢 ⚡"]
        ]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🚕 **Sisteme Hoşgeldiniz.** Menü aşağıdadır.", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LAST_STATUS, LAST_STATUS_TIME
    
    user_id = update.effective_chat.id
    text = update.message.text.strip()
    ALL_USERS.add(user_id)

    if user_id == MERKEZ_ID:
        new_status = ""
        if "DÖNÜŞLER MERKEZ" in text:
            new_status = "🔴 DÖNÜŞLER MERKEZ"
        elif "DÖNÜŞLER AVM" in text:
            new_status = "🔵 DÖNÜŞLER AVM"
        elif "HERKES YERİNE YENİ DURAK" in text:
            new_status = "🟡 HERKES YERİNE YENİ DURAK MERKEZE"
        elif "HERKES YERİNE" in text:
            new_status = "🟢 HERKES YERİNE"
        elif "AKTİF KİŞİ SAYISI" in text:
            await update.message.reply_text(f"📊 **Aktif Kullanıcı Sayısı:** {len(ALL_USERS)}", parse_mode="Markdown")
            return

        if new_status:
            if LAST_STATUS == new_status:
                return

            LAST_STATUS = new_status
            LAST_STATUS_TIME = datetime.now().strftime("%H:%M:%S")

            await update.message.reply_text(f"✅ **Durum Gönderildi:**\n{new_status}", parse_mode="Markdown")

            broadcast_tasks = [
                context.bot.send_message(
                    chat_id=uid,
                    text=f"🔔 **YENİ MERKEZ BİLDİRİMİ**\n\n{new_status}",
                    parse_mode="Markdown"
                )
                for uid in ALL_USERS if uid != MERKEZ_ID
            ]
            if broadcast_tasks:
                await asyncio.gather(*broadcast_tasks, return_exceptions=True)
            return

    if "SON DURUM" in text:
        time_info = f" *(Saat: {LAST_STATUS_TIME})*" if LAST_STATUS_TIME else ""
        await update.message.reply_text(f"📍 **MERKEZİN SON BİLDİRİMİ:**\n\n{LAST_STATUS}{time_info}", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
