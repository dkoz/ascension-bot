import nextcord
from nextcord.ext import commands
from util.eos import AsaProtocol

class ServerStatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Required info for EOS Protocol
        self.client_id = 'xyza7891muomRmynIIHaJB9COBKkwj6n'
        self.client_secret = 'PP5UGxysEieNfSrEicaD1N2Bb3TdXuD7xHYcsdUHZ7s'
        self.deployment_id = 'ad9a8feffb3b4b2ca315546f038c3ae2'
        self.epic_api = 'https://api.epicgames.dev'
        self.asa_protocol = AsaProtocol(self.client_id, self.client_secret, self.deployment_id, self.epic_api)

    # Looking up servers
    @nextcord.slash_command(description='Displays the status of a server.', default_member_permissions=nextcord.Permissions(administrator=True))
    async def queryserver(self, interaction: nextcord.Interaction, host: str, port: int):
        try:
            server_info = await self.asa_protocol.query(host, port)
            embed = self.create_embed(server_info)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error fetching server status: {e}", ephemeral=True)

    def create_embed(self, server_info):
        embed = nextcord.Embed(title="Server Status", color=nextcord.Color.blue())
        embed.add_field(name="Server Name", value=server_info['name'], inline=False)
        embed.add_field(name="Map", value=server_info['map'], inline=True)
        embed.add_field(name="Players", value=f"{server_info['numplayers']}/{server_info['maxplayers']}", inline=True)
        embed.add_field(name="Latency", value=server_info['ping'], inline=True)
        embed.add_field(name="Connect", value=server_info['connect'], inline=True)
        embed.add_field(name="Password", value="Yes" if server_info['password'] else "No", inline=True)

        return embed

def setup(bot):
    bot.add_cog(ServerStatusCog(bot))
