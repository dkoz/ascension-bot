import nextcord
from nextcord.ext import commands
from pydactyl import PterodactylClient
import logging
import os
from dotenv import load_dotenv

# Remember to add the following to your .env file
# You will need to py-dactyl library with pip
load_dotenv()
PTERO_API = os.getenv("PTERO_API")
PTERO_URL = os.getenv("PTERO_URL")
PTERO_WHITELIST = [int(id.strip()) for id in os.getenv("PTERO_WHITELIST", "").split(",")]

logging.basicConfig(level=logging.INFO)

api = PterodactylClient(PTERO_URL, PTERO_API)

class PterodactylControls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def authcheck(self, ctx):
        if ctx.author.id not in PTERO_WHITELIST:
            await ctx.send('You can not use this command!')
            return False
        return True

    async def poweraction(self, ctx, server_id: str, action: str):
        if not await self.authcheck(ctx):
            return
        try:
            response = api.client.servers.send_power_action(server_id, action)
            if response.status_code == 204:
                await ctx.send(f'{action.capitalize()}ing server with ID "{server_id}".')
            else:
                logging.error(f'Unexpected response: {response.status_code} {response.text}')
                await ctx.send(f'Unexpected response: {response.status_code} {response.text}')
        except Exception as e:
            logging.error(f'You have an error: {e}')
            await ctx.send(f'You have an error: {e}')

    @commands.command(description="Start the specified game server.")
    async def startserver(self, ctx, server_id: str):
        await self.poweraction(ctx, server_id, 'start')

    @commands.command(description="Stop the specified game server.")
    async def stopserver(self, ctx, server_id: str):
        await self.poweraction(ctx, server_id, 'stop')

    @commands.command(description="Restart the specified game server.")
    async def restartserver(self, ctx, server_id: str):
        await self.poweraction(ctx, server_id, 'restart')

    @commands.command(description="Kill the specified game server.")
    async def killserver(self, ctx, server_id: str):
        await self.poweraction(ctx, server_id, 'kill')

    @commands.command(description="Displays information about a specified game server.")
    async def info(self, ctx, server_id: str):
        if not await self.authcheck(ctx):
            return
        try:
            server_info = api.client.servers.get_server(server_id)
            stats = api.client.servers.get_server_utilization(server_id)

            if not isinstance(server_info, dict) or not isinstance(stats, dict):
                logging.error(f'Invalid response format: {server_info} or {stats}')
                await ctx.send('Error: Invalid response format from the API.')
                return

            resources = stats.get('resources', {})

            server_details = {
                "Name": server_info.get('name', 'N/A'),
                "Status": server_info.get('status', 'Unknown'),
                "Owner": 'Yes' if server_info.get('server_owner', False) else 'No',
                "Node": server_info.get('node', 'N/A'),
                "CPU Usage": f"{resources.get('cpu_absolute', 'N/A')}%",
                "Memory Usage": f"{resources.get('memory_bytes', 'N/A') / 1024 / 1024:.2f} MB",
                "Disk Usage": f"{resources.get('disk_bytes', 'N/A') / 1024 / 1024:.2f} MB",
                "Network RX": f"{resources.get('network_rx_bytes', 'N/A') / 1024:.2f} KB",
                "Network TX": f"{resources.get('network_tx_bytes', 'N/A') / 1024:.2f} KB",
                "Uptime": f"{resources.get('uptime', 'N/A')} seconds"
            }

            embed = nextcord.Embed(title="Server Details", color=0x00ff00)
            for key, value in server_details.items():
                embed.add_field(name=key, value=value, inline=True)
            embed.set_footer(text=f"Server ID: {server_id}")

            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f'Error: {e}')
            await ctx.send(f'Error: {e}')

def setup(bot):
    bot.add_cog(PterodactylControls(bot))