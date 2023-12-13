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
    async def arkon(self, interaction: nextcord.Interaction):
        pass

    @arkon.subcommand(description="Send a command to the ARK server.")
    async def command(self, interaction: nextcord.Interaction, command: str):
        with MCRcon(self.rcon_host, self.rcon_password, self.rcon_port) as mcr:
            response = mcr.command(command)
            await interaction.response.send_message(f'Response: {response}')

    @arkon.subcommand(description="Send a chat message to the ARK server.")
    async def serverchat(self, interaction: nextcord.Interaction, message: str):
        discord_name = interaction.user.display_name
        chat_command = f"ServerChat [{discord_name}]: {message}"

        with MCRcon(self.rcon_host, self.rcon_password, self.rcon_port) as mcr:
            response = mcr.command(chat_command)
            await interaction.response.send_message(f"Chat message sent: [{discord_name}]: {message}\nServer response: {response}")

    @arkon.subcommand(description="Get a list of online players.")
    async def playerlist(self, interaction: nextcord.Interaction):
        with MCRcon(self.rcon_host, self.rcon_password, self.rcon_port) as mcr:
            response = mcr.command("ListPlayers")
            await interaction.response.send_message(f'Online Players: {response}')

    @arkon.subcommand(description="Broadcast a message to all players.")
    async def broadcast(self, interaction: nextcord.Interaction, message: str):
        with MCRcon(self.rcon_host, self.rcon_password, self.rcon_port) as mcr:
            response = mcr.command(f"Broadcast {message}")
            await interaction.response.send_message(f"Broadcasted message: {message}\nServer response: {response}")

def setup(bot):
    bot.add_cog(ARKRconCog(bot))