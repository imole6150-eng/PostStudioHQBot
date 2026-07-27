import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///poststudio.db")
# Optional: set this to your own numeric Telegram user ID to make the bot
# private (it will ignore/ refuse everyone else). Leave blank to allow anyone.
OWNER_TELEGRAM_ID = os.environ.get("OWNER_TELEGRAM_ID", "").strip()

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError(
        "TELEGRAM_BOT_TOKEN is not set. Add it to your .env file locally, "
        "or to your Railway service Variables."
    )
