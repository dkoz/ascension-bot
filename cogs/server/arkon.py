import json
import os
import nextcord
from nextcord.ext import commands
from gamercon_async import GameRCON
import datetime

class ARKRconCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        config_path = 'config.json'
        with open(config_path) as config_file:
            config = json.load(config_file)
            self.servers = config["RCON_SERVERS"]

    async def rcon_command(self, server_name, command):
        server = self.servers.get(server_name)
        if not server:
            return f"Server '{server_name}' not found."

        try:
            async with GameRCON(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"]) as ac:
                return await ac.send(command)
        except Exception as error:
            return f"Error sending command: {error}"

    async def autocomplete_server(self, interaction: nextcord.Interaction, current: str):
        choices = [server for server in self.servers if current.lower() in server.lower()]
        await interaction.response.send_autocomplete(choices)
    
    @nextcord.slash_command(
        description="Main ARK server command.",
        default_member_permissions=nextcord.Permissions(administrator=True),
        dm_permission=False
    )
    async def arkon(self, _interaction: nextcord.Interaction):
        pass

    @arkon.subcommand(description="Send a remote rcon command.")
    async def rcon(self, interaction: nextcord.Interaction, command: str, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        response = await self.rcon_command(server, command)
        await interaction.response.send_message(f'Response: {response}')

    @rcon.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @arkon.subcommand(description="Send a chat message to the ARK server.")
    async def serverchat(self, interaction: nextcord.Interaction, message: str, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        discord_name = interaction.user.display_name
        chat_command = f"ServerChat [{discord_name}]: {message}"
        response = await self.rcon_command(server, chat_command)
        await interaction.response.send_message(f"Chat message sent: [{discord_name}]: {message}\nServer response: {response}")

    @serverchat.on_autocomplete("server")
    async def on_autocomplete_serverchat(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @arkon.subcommand(description="Kick a player from the ARK server.")
    async def kick(self, interaction: nextcord.Interaction, eos_id: str, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        response = await self.rcon_command(server, f"KickPlayer {eos_id}")
        await interaction.response.send_message(f'Response: {response}')

    @kick.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @arkon.subcommand(description="Ban a player from the ARK server.")
    async def ban(self, interaction: nextcord.Interaction, eos_id: str, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        response = await self.rcon_command(server, f"BanPlayer {eos_id}")
        await interaction.response.send_message(f'Response: {response}')
        
    @ban.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)
        
    @arkon.subcommand(description="Unban a player from the ARK server.")
    async def unban(self, interaction: nextcord.Interaction, eos_id: str, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        response = await self.rcon_command(server, f"UnbanPlayer {eos_id}")
        await interaction.response.send_message(f'Response: {response}')
        
    @unban.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)
        
    @arkon.subcommand(description="Destroy all wild dinos.")
    async def destroydinos(self, interaction: nextcord.Interaction, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        await self.rcon_command(server, "DestroyWildDinos")
        await interaction.response.send_message(f'Destroyed all wild dinos on {server}.')
        
    @destroydinos.on_autocomplete("server")
    async def on_autocomplete_rcon(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @arkon.subcommand(description="Get a list of online players.")
    async def playerlist(self, interaction: nextcord.Interaction, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        response = await self.rcon_command(server, "ListPlayers")
        await interaction.response.send_message(f'Online Players: {response}')

    @playerlist.on_autocomplete("server")
    async def on_autocomplete_playerlist(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @arkon.subcommand(description="Broadcast a message to all players.")
    async def broadcast(self, interaction: nextcord.Interaction, message: str, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        response = await self.rcon_command(server, f"Broadcast {message}")
        await interaction.response.send_message(f"Broadcasted message: {message}\nServer response: {response}")

    @broadcast.on_autocomplete("server")
    async def on_autocomplete_broadcast(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

    @arkon.subcommand(description="Get the game log from an ARK server.")
    async def getgamelog(self, interaction: nextcord.Interaction, server: str = nextcord.SlashOption(description="Select a server", autocomplete=True)):
        await interaction.response.defer(ephemeral=True)
        log_content = await self.rcon_command(server, "GetGameLog")
        if not log_content or "Error" in log_content:
            await interaction.response.send_message(f"Failed to get game log: {log_content}")
            return

        file_name = f"{server}_gamelog_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = os.path.join("logs", file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            file.write(log_content)

        with open(file_path, "rb") as file:
            await interaction.followup.send(file=nextcord.File(file, file_name))

    @getgamelog.on_autocomplete("server")
    async def on_autocomplete_broadcast(self, interaction: nextcord.Interaction, current: str):
        await self.autocomplete_server(interaction, current)

def setup(bot):
    bot.add_cog(ARKRconCog(bot))