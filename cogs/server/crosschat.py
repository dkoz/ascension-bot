import json
import nextcord
from nextcord.ext import commands
from gamercon_async import GameRCON
from util.settings import CHATLOG_CHANNEL
import asyncio
import logging

class CrossChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.channel_id = CHATLOG_CHANNEL

    def load_config(self):
        config_path = 'config.json'
        with open(config_path) as config_file:
            self.config = json.load(config_file)
            self.servers = self.config["RCON_SERVERS"]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != self.channel_id:
            return

        formatted_message = f"[{message.author.display_name}]: {message.content}"

        await self.global_broadcast(formatted_message)

    async def global_broadcast(self, message):
        for server_name, server_details in self.servers.items():
            try:
                async with GameRCON(server_details["RCON_HOST"], server_details["RCON_PORT"], server_details["RCON_PASS"]) as ac:
                    server_chat_command = f"ServerChat {message}"
                    await ac.send(server_chat_command)
                    logging.info(f"Message sent to {server_name}: {message}")
            except Exception as e:
                logging.error(f"Failed to send message to {server_name}: {e}")

def setup(bot):
    bot.add_cog(CrossChatCog(bot))
