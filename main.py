import os
import re
import threading
import requests
from flask import Flask
import telebot

TOKEN = "8638144587:AAEgj-Z6JnICpSXMbWCvUOh0YgZjrUM9M6Y"
bot = telebot.TeleBot(TOKEN)

# Создаем мини-сервер, чтобы облачный хостинг видел активность
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is active!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


def is_tiktok_url(url):
  pattern = r"https?://(www\.|vm\.|vt\.)?tiktok\.com/.*"
  return re.match(pattern, url) is not None


def get_tiktok_no_watermark_url(tiktok_url):
  api_url = "https://tikwm.com/api/"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }
  try:
    response = requests.post(
        api_url, data={"url": tiktok_url, "hd": 1}, headers=headers
    )
    data = response.json()
    if data.get("code") == 0:
      return data["data"]["play"]
  except Exception as e:
    print(f"Ошибка API: {e}")
  return None


@bot.message_handler(commands=["start"])
def start_cmd(message):
  bot.send_message(
      message.chat.id,
      f"Привет, {message.from_user.first_name}! 👋\n\n"
      "Пришли мне ссылку на видео из TikTok, и я скачаю его **без водяного знака**!",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
  url = message.text.strip()

  if is_tiktok_url(url):
    status_msg = bot.send_message(
        message.chat.id, "⏳ Качаю видео без водяного знака..."
    )
    try:
      video_url = get_tiktok_no_watermark_url(url)
      if video_url:
        video_bytes = requests.get(video_url).content
        file_path = "video.mp4"

        with open(file_path, "wb") as f:
          f.write(video_bytes)

        with open(file_path, "rb") as video_file:
          bot.send_video(message.chat.id, video_file)

        bot.delete_message(message.chat.id, status_msg.message_id)
        if os.path.exists(file_path):
          os.remove(file_path)
      else:
        bot.edit_message_text(
            "❌ Не удалось скачать видео. Проверь ссылку.",
            message.chat.id,
            status_msg.message_id,
        )
    except Exception as e:
      print(f"Ошибка: {e}")
      bot.edit_message_text(
          "⚠️ Произошла ошибка при обработке видео.",
          message.chat.id,
          status_msg.message_id,
      )
  else:
    bot.send_message(
        message.chat.id, "Пожалуйста, отправь правильную ссылку на TikTok!"
    )


if __name__ == "__main__":
  # Запускаем веб-сервер в фоновом потоке
  t = threading.Thread(target=run_flask)
  t.daemon = True
  t.start()

  print("Бот запущен в облачном режиме...")
  bot.infinity_polling()