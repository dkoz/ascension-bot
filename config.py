import os
from dotenv import load_dotenv

#Load Environment Variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_PREFIX = os.getenv("BOT_PREFIX")
CHATLOG_CHANNEL = int(os.getenv("CHATLOG_CHANNEL"))
whitelist_env = os.getenv("WHITELIST_GUILDS", "")
whitelist = [int(guild_id) for guild_id in whitelist_env.split(',') if guild_id.isdigit()]