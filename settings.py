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
whitelist_env = os.getenv("WHITELIST_GUILDS", "")
whitelist = [int(guild_id) for guild_id in whitelist_env.split(',') if guild_id.isdigit()]
PTERO_API = os.getenv("PTERO_API", "No API Found")
PTERO_URL = os.getenv("PTERO_URL", "No URL Found")
PTERO_WHITELIST = [int(id.strip()) for id in os.getenv("PTERO_WHITELIST", "").split(",") if id.strip().isdigit()]