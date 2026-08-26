import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==========================================
# TELEGRAM ID VE BOT AYARLARI
# ==========================================
BOT_TOKEN = "8922084774:AAGJRthYR1LH9O2ZhyE3JwBVzfsZ8jwzse4"

MERKEZ_ID = 8860608922     # Merkez Telefonu ID
MY_ADMIN_ID = 8955129085   # Yönetici (Sizin) ID

DATA_FILE = "registered_drivers.json"
STATUS_FILE = "last_status.json"

# Kayıtlı sürücüleri sıfırla ve dosyayı temizle
def reset_and_init_drivers():
    drivers = {}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(drivers, f, ensure_ascii=False, indent=4)
    return drivers

def load_drivers():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_drivers(drivers):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(drivers, f, ensure_ascii=False, indent=4)

def save_last_status(status_text, user_name):
    now_str = datetime.now().strftime("%H:%M")
    status_data = {
        "text": status_text,
        "user": user_name,
        "time": now_str
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=4)

def get_last_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# Listeyi sıfırdan başlatıyoruz
registered_drivers = reset_and_init_drivers()

# ==========================================
# MENÜLER (YETKİYE GÖRE AYRI MENÜ)
# ==========================================
def get_keyboard_for_user(user_id: int):
    # Yönetici veya Merkez ise tam menü gösterilir
    if user_id == MY_ADMIN_ID or user_id == MERKEZ_ID:
        keyboard = [
            ["🔴 DÖNÜŞLER MERKEZ"],
            ["🔵 DÖNÜŞLER AVM"],
            ["🟢 HERKES YERİNE"],
            ["🟡 HERKES YERİNE YENİ DURAK MERKEZE"],
            ["🔍 SON DURUM", "📊 AKTİF KİŞİ SAYISI"]
        ]
    else:
        # Diğer tüm sürücülerde SADECE Son Durum butonu bulunur
        keyboard = [
            ["🔍 SON DURUM"]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==========================================
# START KOMUTU (ONAY KONTROLÜ)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    first_name = user.first_name or "Kullanıcı"

    if user.id == MY_ADMIN_ID or user.id == MERKEZ_ID:
        role_title = "Yönetici" if user.id == MY_ADMIN_ID else "Merkez"
        await update.message.reply_text(
            f"🚖 **Merhaba {first_name} ({role_title} Panelindesiniz)**",
            reply_markup=get_keyboard_for_user(user.id),
            parse_mode="Markdown"
        )
        return

    if user_id in registered_drivers:
        await update.message.reply_text(
            f"🚖 Merhaba {first_name}, Taksi Otomasyon Sistemine Hoş Geldiniz.",
            reply_markup=get_keyboard_for_user(user.id)
        )
        return

    await update.message.reply_text(
        "⏳ **Erişim Talebiniz Alındı.**\nSistemi kullanabilmeniz için yöneticinin onayı bekleniyor..."
    )

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Onayla", callback_data=f"APPROVE_{user_id}_{first_name}"),
            InlineKeyboardButton("❌ Reddet", callback_data=f"REJECT_{user_id}_{first_name}")
        ]
    ])

    await context.bot.send_message(
        chat_id=MY_ADMIN_ID,
        text=f"🚨 **Yeni Sürücü Erişim Talebi!**\n\n"
             f"👤 **Adı:** {first_name}\n"
             f"🆔 **ID:** `{user_id}`\n"
             f"👤 **Kullanıcı Adı:** @{user.username if user.username else 'Yok'}\n\n"
             f"Bu sürücünün bota erişimini onaylıyor musunuz?",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )

# ==========================================
# ALT MENÜ BUTONLARI VE MESAJ İŞLEMCİSİ
# ==========================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    user_id = str(user.id)

    # Onay kontrolü
    if user.id != MY_ADMIN_ID and user.id != MERKEZ_ID and user_id not in registered_drivers:
        await update.message.reply_text("🚫 Sisteme kayıtlı değilsiniz veya onay bekliyorsunuz.")
        return

    # --- AKTİF KİŞİ SAYISI (SADECE ADMİN/MERKEZ) ---
    if text == "📊 AKTİF KİŞİ SAYISI":
        if user.id == MY_ADMIN_ID or user.id == MERKEZ_ID:
            merkez_str_id = str(MERKEZ_ID)
            admin_str_id = str(MY_ADMIN_ID)

            drivers_list = {k: v for k, v in registered_drivers.items() if k not in [merkez_str_id, admin_str_id]}
            total_count = len(drivers_list)

            msg = f"📊 **AKTİF SÜRÜCÜ DURUMU**\n"
            msg += f"👑 Merkez ve Yönetici Hariç Sürücü Sayısı: **{total_count}**\n\n"

            if total_count > 0:
                msg += "📋 **Kayıtlı Sürücü Listesi:**\n"
                for d_id, d_name in drivers_list.items():
                    msg += f"• **{d_name}** — ID: `{d_id}`\n"
            else:
                msg += "_Henüz onaylanmış sürücü bulunmuyor._"

            await update.message.reply_text(msg, parse_mode="Markdown")

    # --- SON DURUM SORGULAMA ---
    elif text == "🔍 SON DURUM":
        last_status = get_last_status()
        if last_status:
            await update.message.reply_text(
                f"📢 **EN SON DURUM BİLDİRİMİ**\n\n"
                f"👤 **Gönderen:** {last_status['user']}\n"
                f"📌 **Durum:** {last_status['text']}\n"
                f"⏰ **Saat:** {last_status['time']}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("ℹ️ Henüz girilmiş bir durum bildirimi bulunmuyor.")

    # --- DURUM BUTONLARI (SADECE ADMİN VE MERKEZ KULLANABİLİR) ---
    elif text in [
        "🔴 DÖNÜŞLER MERKEZ",
        "🔵 DÖNÜŞLER AVM",
        "🟢 HERKES YERİNE",
        "🟡 HERKES YERİNE YENİ DURAK MERKEZE"
    ]:
        if user.id != MY_ADMIN_ID and user.id != MERKEZ_ID:
            await update.message.reply_text("🚫 Bu butonları kullanma yetkiniz yoktur.")
            return

        save_last_status(text, user.first_name)
        notification_text = f"📢 **DURUM GÜNCELLEMESİ**\n👤 {user.first_name}: {text}"

        await update.message.reply_text(f"{user.first_name}: {text}")

        # Onaylı sürücülere bildirimi gönder
        all_recipients = set(registered_drivers.keys())
        all_recipients.add(str(MY_ADMIN_ID))
        all_recipients.add(str(MERKEZ_ID))
        all_recipients.discard(user_id)

        for recipient_id in all_recipients:
            try:
                await context.bot.send_message(
                    chat_id=int(recipient_id),
                    text=notification_text,
                    parse_mode="Markdown"
                )
            except Exception:
                pass

# ==========================================
# ONAY / RED İŞLEMLERİ
# ==========================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data

    if data.startswith("APPROVE_"):
        if user.id != MY_ADMIN_ID:
            await query.answer("Bu işlemi sadece Yönetici onaylayabilir!", show_alert=True)
            return

        _, target_id, target_name = data.split("_", 2)
        registered_drivers[target_id] = target_name
        save_drivers(registered_drivers)

        await query.edit_message_text(f"✅ **{target_name}** (`{target_id}`) sürücüsü onaylandı ve sisteme eklendi.")

        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text="🎉 **Erişim Talebiniz Onaylandı!**\nSistemi kullanabilirsiniz. Başlamak için /start yazabilirsiniz.",
                reply_markup=get_keyboard_for_user(int(target_id))
            )
        except Exception:
            pass
        return

    elif data.startswith("REJECT_"):
        if user.id != MY_ADMIN_ID:
            await query.answer("Bu işlemi sadece Yönetici reddedebilir!", show_alert=True)
            return

        _, target_id, target_name = data.split("_", 2)
        await query.edit_message_text(f"❌ **{target_name}** (`{target_id}`) sürücüsünün talebi reddedildi.")
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text="🚫 **Erişim Talebiniz Reddedildi.**"
            )
        except Exception:
            pass
        return

# ==========================================
# ANA ÇALIŞTIRICI
# ==========================================
def main():
    print("Bot çalışıyor...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
