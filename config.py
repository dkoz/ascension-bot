import os
from dotenv import load_dotenv

#Load Environment Variables
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
bot_prefix = os.getenv("BOT_PREFIX")
RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
RCON_PASS = os.getenv("RCON_PASS")
CHATLOG_CHANNEL = int(os.getenv("CHATLOG_CHANNEL"))
whitelist_env = os.getenv("WHITELIST_GUILDS", "")
whitelist = [int(guild_id) for guild_id in whitelist_env.split(',') if guild_id.isdigit()]