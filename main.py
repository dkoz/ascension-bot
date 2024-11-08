import nextcord
from nextcord.ext import commands
import sys
import traceback
import os
import settings
import importlib.util
from util.errorhandling import setup_logging

setup_logging()

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=settings.BOT_PREFIX, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}, created by koz')
    activity = nextcord.Game(name=settings.BOT_STATUS)
    await bot.change_presence(activity=activity)

@bot.event
async def on_guild_join(guild):
    print(f"Joined guild: {guild.name} (ID: {guild.id})")

@bot.event
async def on_guild_remove(guild):
    print(f"Left guild: {guild.name} (ID: {guild.id})")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, nextcord.Forbidden):
        await ctx.send("I lack the necessary permissions to perform this action.")
    else:
        print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

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
    bot.run(settings.BOT_TOKEN)