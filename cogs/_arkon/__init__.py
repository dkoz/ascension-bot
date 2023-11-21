import nextcord
from nextcord.ext import commands
from lib.mcrcon import MCRcon
from main import RCON_HOST, RCON_PORT, RCON_PASS

class ARKRconCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rcon_password = RCON_PASS
        self.rcon_host = RCON_HOST
        self.rcon_port = RCON_PORT

    @nextcord.slash_command(description="Main ARK server command.", default_member_permissions=nextcord.Permissions(administrator=True))
    async def arkcmd(self, interaction: nextcord.Interaction):
        pass

    @arkcmd.subcommand(description="Send a command to the ARK server.")
    async def command(self, interaction: nextcord.Interaction, command: str):
        with MCRcon(self.rcon_host, self.rcon_password, self.rcon_port) as mcr:
            response = mcr.command(command)
            await interaction.response.send_message(f'Response: {response}')

    @arkcmd.subcommand(description="Send a chat message to the ARK server.")
    async def serverchat(self, interaction: nextcord.Interaction, message: str):
        chat_command = f"ServerChat {message}"  # Modify this if your server uses a different command format
        with MCRcon(self.rcon_host, self.rcon_password, self.rcon_port) as mcr:
            response = mcr.command(chat_command)
            await interaction.response.send_message(f"Chat message sent: {message}\nServer response: {response}")

def setup(bot):
    bot.add_cog(ARKRconCog(bot))