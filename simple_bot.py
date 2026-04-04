import os
import asyncio
import logging
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Переменные окружения (всё берётся из настроек Render)
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
URL = "https://telegram-bot-ancj.onrender.com"  # ВАШ АДРЕС
PORT = 8000

# --- Обработчики команд Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на команду /start"""
    await update.message.reply_text("Привет! Я бот для генерации картинок! 🎉\nОтправь мне любой запрос, и я создам изображение.")

# --- Настройка веб-сервера и вебхука ---
async def main():
    # Создаём приложение Telegram-бота
    app = Application.builder().token(TOKEN).updater(None).build()
    app.add_handler(CommandHandler("start", start))

    # Устанавливаем вебхук
    webhook_url = f"{URL}/telegram"
    await app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logging.info(f"Webhook set to {webhook_url}")

    # Создаём веб-сервер для приёма сообщений от Telegram
    async def telegram(request: Request) -> Response:
        """Принимает сообщения от Telegram"""
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.update_queue.put(update)
        return Response()

    async def health(_: Request) -> PlainTextResponse:
        """Health check для Render"""
        return PlainTextResponse("OK")

    starlette_app = Starlette(routes=[
        Route("/telegram", telegram, methods=["POST"]),
        Route("/healthcheck", health, methods=["GET"]),
    ])

    # Запускаем веб-сервер
    import uvicorn
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)

    async with app:
        await app.start()
        await server.serve()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
