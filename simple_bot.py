import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# Простой обработчик команды /start
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    try:
        update = request.get_json()
        if "message" in update and "text" in update["message"]:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"]["text"]

            if text == "/start":
                reply = "Привет! Я тестовый бот. Если ты это видишь, то связь работает! 🎉"
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                data = {"chat_id": chat_id, "text": reply}
                requests.post(url, json=data)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
   
