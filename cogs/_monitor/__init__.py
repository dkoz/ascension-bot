import nextcord
from nextcord.ext import commands, tasks
from lib.eos import AsaProtocol
import os
import json

def save_guild_info(guild_id, channel_id, message_id, host, port):
    directory = 'data'
    filepath = os.path.join(directory, 'server_info.json')

    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    guild_data = data.get(str(guild_id), [])
    guild_data.append({
        'channel_id': channel_id,
        'message_id': message_id,
        'server': {
            'host': host,
            'port': port
        }
    })
    data[str(guild_id)] = guild_data

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def load_guild_info(guild_id):
    directory = 'data'
    filepath = os.path.join(directory, 'server_info.json')

    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get(str(guild_id))
    except FileNotFoundError:
        return None

class MonitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Required info for EOS Protocol
        self.client_id = 'xyza7891muomRmynIIHaJB9COBKkwj6n'
        self.client_secret = 'PP5UGxysEieNfSrEicaD1N2Bb3TdXuD7xHYcsdUHZ7s'
        self.deployment_id = 'ad9a8feffb3b4b2ca315546f038c3ae2'
        self.epic_api = 'https://api.epicgames.dev'
        self.asa_protocol = AsaProtocol(self.client_id, self.client_secret, self.deployment_id, self.epic_api)
        # Task start for server status.
        self.update_server_status.start()

    # Time before each server querty.
    @tasks.loop(minutes=5)
    async def update_server_status(self):
        print(f"Fetching server information.")
        for guild in self.bot.guilds:
            guild_info_list = load_guild_info(guild.id)
            if guild_info_list:
                for guild_info in guild_info_list:
                    channel = self.bot.get_channel(int(guild_info['channel_id']))
                    if channel:
                        try:
                            message = await channel.fetch_message(int(guild_info['message_id']))
                            server_info = await self.asa_protocol.query(guild_info['server']['host'], guild_info['server']['port'])
                            embed = self.create_embed(server_info)
                            await message.edit(embed=embed)
                        except nextcord.NotFound:
                            # When message is not found, attempt to repost it.
                            try:
                                server_info = await self.asa_protocol.query(guild_info['server']['host'], guild_info['server']['port'])
                                embed = self.create_embed(server_info)
                                new_message = await channel.send(embed=embed)
                                save_guild_info(guild.id, channel.id, new_message.id, guild_info['server']['host'], guild_info['server']['port'])
                            except Exception as e:
                                print(f"Error reposting server status for guild {guild.id}: {e}")
                        except Exception as e:
                            print(f"Error updating server status for guild {guild.id}: {e}")

    @update_server_status.before_loop
    async def before_update_server_status(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.update_server_status.cancel()
    
    @nextcord.slash_command(description='Create looping embed of your server status.', default_member_permissions=nextcord.Permissions(administrator=True))
    async def postserver(self, interaction: nextcord.Interaction, host: str, port: int, channel: nextcord.TextChannel):
        try:
            server_info = await self.asa_protocol.query(host, port)
            embed = self.create_embed(server_info)
            message = await channel.send(embed=embed)
            save_guild_info(interaction.guild_id, channel.id, message.id, host, port)
            await interaction.response.send_message(f"Server status sent to {channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error fetching server status: {e}", ephemeral=True)
    
    # Weird embed, it does need updating.
    def create_embed(self, server_info):
        embed = nextcord.Embed(title="Server Status", color=nextcord.Color.blue())
        embed.add_field(name=server_info['name'], value="", inline=False)
        embed.add_field(name="Map", value=server_info['map'], inline=True)
        embed.add_field(name="Players", value=f"{server_info['numplayers']}/{server_info['maxplayers']}", inline=True)
        embed.add_field(name="Latency", value=server_info['ping'], inline=True)
        embed.add_field(name="Connect", value=server_info['connect'], inline=True)
        embed.add_field(name="Password", value="Yes" if server_info['password'] else "No", inline=True)
        embed.add_field(name="Last Wipe", value="<t:1698530400:R>", inline=True)
        embed.set_image(url="https://cdn.cloudflare.steamstatic.com/steam/apps/2399830/header.jpg?t=1699643475")

        return embed

def setup(bot):
    bot.add_cog(MonitorCog(bot))
