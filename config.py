import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# SMMBox API
SMMBOX_API_TOKEN = os.getenv('SMMBOX_API_TOKEN')
SMMBOX_API_URL = 'https://smmbox.com/api/v1'

# Настройки постинга
POSTS_PER_DAY = 7

# Проверка наличия обязательных переменных
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле")
if not SMMBOX_API_TOKEN:
    raise ValueError("SMMBOX_API_TOKEN не найден в .env файле")