import nextcord
from nextcord.ext import commands
import os
import config
import importlib.util

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}, created by koz')
    activity = nextcord.Game(name=config.BOT_STATUS)
    await bot.change_presence(activity=activity)

def has_setup_function(module_name):
    module_spec = importlib.util.find_spec(module_name)
    if module_spec is None:
        return False
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return hasattr(module, 'setup')

for entry in os.listdir("cogs"):
    if entry.endswith('.py'):
        module_name = f"cogs.{entry[:-3]}"
        if has_setup_function(module_name):
            bot.load_extension(module_name)
    elif os.path.isdir(f"cogs/{entry}"):
        for filename in os.listdir(f"cogs/{entry}"):
            if filename.endswith('.py'):
                module_name = f"cogs.{entry}.{filename[:-3]}"
                if has_setup_function(module_name):
                    bot.load_extension(module_name)

if __name__ == "__main__":
    bot.run(config.BOT_TOKEN)