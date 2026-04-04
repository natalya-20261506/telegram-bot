import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
PRICE_PER_IMAGE = 20

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

user_requests = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Привет! Отправь текст, и я создам картинку. Цена: 20 Stars.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    user_id = update.effective_user.id
    user_requests[user_id] = prompt

    keyboard = [[InlineKeyboardButton(f"💎 Оплатить {PRICE_PER_IMAGE} Stars", pay=True)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_invoice(
        chat_id=user_id,
        title="Генерация изображения",
        description=f"Запрос: {prompt[:100]}",
        payload=f"image_{user_id}",
        provider_token="",
        currency="XTR",
        prices=[{"label": "Генерация", "amount": PRICE_PER_IMAGE}],
        reply_markup=reply_markup
    )

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("🎨 Генерирую...")

    if user_id not in user_requests:
        await update.message.reply_text("❌ Ошибка")
        return

    prompt = user_requests[user_id]

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url
        await update.message.reply_photo(photo=image_url, caption=f"✅ Готово! Запрос: {prompt[:200]}")
        del user_requests[user_id]
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    logging.info("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()