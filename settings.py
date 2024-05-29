import os
from dotenv import load_dotenv

#Load Environment Variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "No Token Found")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
BOT_STATUS = os.getenv("BOT_STATUS", "Playing Ark")
CHATLOG_CHANNEL = int(os.getenv("CHATLOG_CHANNEL", 0))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "No webhook set")
WEBHOOK_AVATAR = os.getenv("WEBHOOK_AVATAR", "https://i.imgur.com/ToUflov.png")