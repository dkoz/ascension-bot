import nextcord
from nextcord.ext import commands
import os
import config

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents, help_command=None)

#No need to edit anything below here
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}, created by koz')
    activity = nextcord.Game(name="Playing Ark")
    await bot.change_presence(activity=activity)
    
for folder in os.listdir("cogs"):
    bot.load_extension(f"cogs.{folder}")

if __name__ == "__main__":
    bot.run(config.BOT_TOKEN)