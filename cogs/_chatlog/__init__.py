import nextcord
from nextcord.ext import commands, tasks
from lib.mcrcon import MCRcon
from main import RCON_HOST, RCON_PORT, RCON_PASS, CHATLOG_CHANNEL
import asyncio

class ChatLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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
            'RCON: Not connected'
        ]
        self.prefix = 'YourPrefix'
        self.suffix = 'YourSuffix'
        self.get_chat.start()
        self.rcon_cooldown = 320

    @tasks.loop(seconds=1)
    async def get_chat(self):
        await self.bot.wait_until_ready()
        await self.send_rcon_command("GetChat")

    async def send_rcon_command(self, command):
        try:
            with MCRcon(RCON_HOST, RCON_PASS, RCON_PORT) as mcr:
                response = mcr.command(command)
                await self.parse_message(response)
        except Exception as error:
            print('Error:', error)
            await asyncio.sleep(self.rcon_cooldown)

    async def parse_message(self, res):
        if "Server received, But no response!!" not in res:
            channel = self.bot.get_channel(self.channel_id)
            if channel and not any(filter_word in res for filter_word in self.filters):
                await channel.send(res)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id != self.channel_id:
            return
        command = f"ChatLogAppend {self.prefix}{message.author.display_name}: {message.content} {self.suffix}"
        await self.send_rcon_command(command)

    def cog_unload(self):
        self.get_chat.cancel()

def setup(bot):
    bot.add_cog(ChatLogCog(bot))