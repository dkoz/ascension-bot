import nextcord
from nextcord.ext import commands
import os
import config

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}, created by koz')
    activity = nextcord.Game(name=config.BOT_STATUS)
    await bot.change_presence(activity=activity)

for entry in os.listdir("cogs"):
    if entry.endswith('.py'):
        bot.load_extension(f"cogs.{entry[:-3]}")
    elif os.path.isdir(f"cogs/{entry}"):
        for filename in os.listdir(f"cogs/{entry}"):
            if filename.endswith('.py'):
                bot.load_extension(f"cogs.{entry}.{filename[:-3]}")

if __name__ == "__main__":
    bot.run(config.BOT_TOKEN)