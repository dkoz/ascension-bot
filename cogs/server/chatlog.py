import json
import os
import nextcord
from nextcord.ext import commands, tasks
from config import CHATLOG_CHANNEL
from gamercon_async import GameRCON
import asyncio

class ChatLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.channel_id = CHATLOG_CHANNEL
        self.filters = [
            'Server received, But no response!!',
            'AdminCmd',
            'Tribe Tamed a',
            'Tribe ',
            'Tamed a',
            'was killed!',
            'added to the Tribe',
            'RichColor',
            'RCON: Not connected',
            'froze'
        ]
        self.rcon_cooldown = 320
        self.get_chat.start()

    def load_config(self):
        config_path = 'config.json'
        with open(config_path) as config_file:
            config = json.load(config_file)
            self.servers = config["RCON_SERVERS"]

    @tasks.loop(seconds=1)
    async def get_chat(self):
        await self.bot.wait_until_ready()
        for server_name in self.servers:
            await self.send_rcon_command(server_name, "GetChat")

    async def send_rcon_command(self, server_name, command):
        server = self.servers[server_name]
        try:
            async with GameRCON(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"]) as ac:
                response = await ac.send(command)
                await self.parse_message(server_name, response)
        except Exception as error:
            print(f'Error in {server_name}:', error)
            await asyncio.sleep(self.rcon_cooldown)

    async def parse_message(self, server_name, res):
        if "Server received, But no response!!" not in res:
            channel = self.bot.get_channel(self.channel_id)
            if channel and not any(filter_word in res for filter_word in self.filters):
                formatted_message = f"**[{server_name}]** {res}"
                await channel.send(formatted_message)

    def cog_unload(self):
        self.get_chat.cancel()

def setup(bot):
    bot.add_cog(ChatLogCog(bot))