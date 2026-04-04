import os
import asyncio
import logging
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- НАСТРОЙКИ (из переменных окружения Render) ---
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
URL = os.environ.get("RENDER_EXTERNAL_URL", "https://telegram-bot-ancj.onrender.com")
PORT = int(os.environ.get("PORT", 8000))

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- ОБРАБОТЧИКИ КОМАНД ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие"""
    await update.message.reply_text(
        "🤖 *Привет! Я бот для генерации картинок.*\n\n"
        "Отправь мне любое описание, и я создам изображение.\n"
        "💰 Цена: 20 Telegram Stars за картинку.\n\n"
        "Просто напиши, что ты хочешь увидеть.",
        parse_mode="Markdown"
    )

# --- ОСНОВНАЯ ФУНКЦИЯ ---
async def main():
    # Создаём приложение Telegram-бота
    app = Application.builder().token(TOKEN).updater(None).build()
    app.add_handler(CommandHandler("start", start))

    # --- НАСТРОЙКА ВЕБХУКА И ВЕБ-СЕРВЕРА ---
    # 1. Сообщаем Telegram адрес для приёма обновлений
    webhook_url = f"{URL}/telegram"
    await app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logging.info(f"Webhook set to {webhook_url}")

    # 2. Создаём функцию для обработки входящих сообщений от Telegram
    async def telegram_webhook(request: Request) -> Response:
        """Принимает POST-запросы от Telegram"""
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return Response()

    # 3. Создаём функцию для healthcheck (чтобы Render не "усыплял" бота)
    async def healthcheck(request: Request) -> PlainTextResponse:
        return PlainTextResponse("OK")

    # 4. Собираем веб-приложение Starlette с правильными маршрутами
    starlette_app = Starlette(routes=[
        Route("/telegram", telegram_webhook, methods=["POST"]),  # Telegram шлёт POST-запросы
        Route("/healthcheck", healthcheck, methods=["GET"]),     # Render проверяет GET-запросы
    ])

    # 5. Запускаем веб-сервер Uvicorn
    import uvicorn
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)

    async with app:
        await app.start()
        await server.serve()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
