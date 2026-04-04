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

# Переменные окружения
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render даёт этот адрес автоматически
PORT = 8000  # Render ожидает порт 8000

# --- Обработчики команд Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ на команду /start"""
    await update.message.reply_text("Привет! Я бот для генерации картинок! 🎉")

async def main():
    # Создаём приложение Telegram-бота
    app = Application.builder().token(TOKEN).updater(None).build()
    app.add_handler(CommandHandler("start", start))

    # Устанавливаем вебхук (Telegram будет присылать сообщения на этот адрес)
    await app.bot.set_webhook(url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES)
    logging.info(f"Webhook set to {URL}/telegram")

    # Создаём веб-сервер для приёма сообщений от Telegram
    async def telegram(request: Request) -> Response:
        """Принимает сообщения от Telegram"""
        await app.update_queue.put(Update.de_json(await request.json(), app.bot))
        return Response()

    async def health(_: Request) -> PlainTextResponse:
        """Health check для Render (чтобы сервис не перезапускался)"""
        return PlainTextResponse("OK")

    starlette_app = Starlette(routes=[
        Route("/telegram", telegram, methods=["POST"]),
        Route("/healthcheck", health, methods=["GET"]),
    ])

    # Запускаем веб-сервер
    import uvicorn
    web = uvicorn.Server(uvicorn.Config(starlette_app, host="0.0.0.0", port=PORT, log_level="info"))
    
    async with app:
        await app.start()
        await web.serve()
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
      
