import nextcord
from nextcord.ext import commands
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

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=bot_prefix, intents=intents)

#No need to edit anything below here
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    activity = nextcord.Game(name="Playing Ark")
    await bot.change_presence(activity=activity)
    
for folder in os.listdir("cogs"):
    bot.load_extension(f"cogs.{folder}")

if __name__ == "__main__":
    bot.run(bot_token)