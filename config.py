import os
from dotenv import load_dotenv

# загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL", "sqlite:///tasks.db")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
YOOKASSA_TOKEN = os.getenv("YOOKASSA_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
SHOP_ID = os.getenv("SHOP_ID")

if not BOT_TOKEN:
    raise RuntimeError("SECRET_KEY is not set in environment")

if not BOT_TOKEN:
    raise RuntimeError("SHOP_ID is not set in environment")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set in environment")

if not YOOKASSA_TOKEN:
    raise RuntimeError("YOOKASSA_TOKEN is not set in enviroment")
