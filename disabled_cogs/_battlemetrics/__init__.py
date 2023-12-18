import nextcord
from nextcord.ext import commands, tasks
from .lib import battlemetrics
import json
import os

class BattleMetricsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_file = "data/battlemetrics.json"
        self.servers = self.load_config()
        self.update_server_info.start()
        self.bot.loop.create_task(self.update_servers())

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                return json.load(file)
        return {}

    def save_config(self):
        with open(self.config_file, "w") as file:
            json.dump(self.servers, file, indent=4)

    async def send_debug_message(self, message):
        debug_channel = self.bot.get_channel(1109959557754654784)
        if debug_channel:
            await debug_channel.send(message)

    async def update_servers(self):
        for guild_id, servers in self.servers.items():
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            for server in servers:
                try:
                    bmapi = battlemetrics
                    await bmapi.setup(server['bearer_token'])

                    response = await bmapi.server_info(server['battlemetrics_server_id'])
                    if 'data' in response:
                        server_info = response['data']['attributes']
                        online_status = server_info.get('status', 'N/A')

                        embed = nextcord.Embed(title="Server Info", color=0xF3A316)
                        embed.add_field(name="Server Name", value=server_info.get('name', 'N/A'), inline=False)
                        embed.add_field(name="Players Online", value=f"{server_info.get('players', 0)}/{server_info.get('maxPlayers', 0)}", inline=True)
                        embed.add_field(name="Map", value=server_info.get('details', {}).get('map', 'N/A'), inline=True)
                        embed.add_field(name="Status", value=online_status, inline=True)
                        embed.add_field(name="Version", value=server_info.get('details', {}).get('version', 'N/A'), inline=True)
                        embed.add_field(name="Crossplay", value=server_info.get('details', {}).get('crossplay', 'N/A'), inline=True)
                        embed.add_field(name="Connection", value=f"{server_info.get('ip', 'N/A')}:{server_info.get('port', 'N/A')}", inline=True)
                        embed.set_image(url=server['embed_image_url'])

                        if 'modNames' in server_info.get('details', {}) and 'modLinks' in server_info.get('details', {}):
                            mod_strings = [f"[{mod_name}]({mod_link})" for mod_name, mod_link in zip(server_info['details']['modNames'], server_info['details']['modLinks'])]
                            mod_text = ""
                            field_count = 0
                            for mod_string in mod_strings:
                                if len(mod_text) + len(mod_string) + 1 > 1024:
                                    embed.add_field(name=f"Mods (Part {field_count + 1})", value=mod_text, inline=False)
                                    mod_text = mod_string + "\n"
                                    field_count += 1
                                else:
                                    mod_text += mod_string + "\n"
                            if mod_text:
                                embed.add_field(name=f"Mods (Part {field_count + 1})", value=mod_text, inline=False)
                        else:
                            embed.add_field(name="Mods", value="No mod information available", inline=False)

                        channel = self.bot.get_channel(server['discord_channel_id'])
                        if channel is None:
                            await self.send_debug_message(f"Channel ID {server['discord_channel_id']} not found.")
                            continue

                        try:
                            if server.get('message_id'):
                                try:
                                    message = await channel.fetch_message(server['message_id'])
                                    await message.edit(embed=embed)
                                except nextcord.NotFound:
                                    await self.send_debug_message(f"Message ID {server['message_id']} not found. Sending new message.")
                                    message = await channel.send(embed=embed)
                                    server['message_id'] = message.id
                            else:
                                message = await channel.send(embed=embed)
                                server['message_id'] = message.id
                        except Exception as e:
                            await self.send_debug_message(f"Error sending message in channel {server['discord_channel_id']}: {e}")

                except Exception as e:
                    await self.send_debug_message(f"Error updating server info for guild {guild_id}: {e}")

    @tasks.loop(minutes=1)
    async def update_server_info(self):
        await self.update_servers()
                        
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def setserver(self, ctx, battlemetrics_server_id: str, discord_channel_id: int, bearer_token: str, embed_image_url: str):
        new_server = {
            "battlemetrics_server_id": battlemetrics_server_id,
            "discord_channel_id": discord_channel_id,
            "bearer_token": bearer_token,
            "embed_image_url": embed_image_url,
            "message_id": None
        }
        self.servers.setdefault(ctx.guild.id, []).append(new_server)
        self.save_config()
        await ctx.send("Server configuration added.")
            
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def rcon(self, ctx, server_id: str, *, command: str):
        """Sends an RCON command to the specified server."""
        bmapi = battlemetrics

        servers = await self.config.guild(ctx.guild).servers()
        server_config = next((s for s in servers if s['battlemetrics_server_id'] == server_id), None)

        if server_config is None:
            await ctx.send("Server configuration not found.")
            return

        await bmapi.setup(server_config['bearer_token'])
        response = await bmapi.server_send_console_command(server_id=server_id, command=command)

        if 'errors' in response:
            error_message = f"There was an error with that command!\n**RESPONSE**\n{response['errors'][0]['detail']}"
            await ctx.send(f"{ctx.author.mention} something went wrong:\n{error_message}")
        else:
            result_message = f"Successfully ran the command!\n**RESULTS**\n{response['data']['attributes']['result']}"
            await ctx.send(result_message)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def banlist(self, ctx, battlemetrics_server_id: str):
        """Fetches and displays the ban list for the specified server."""
        servers = await self.config.guild(ctx.guild).servers()
        server_config = next((s for s in servers if s['battlemetrics_server_id'] == battlemetrics_server_id), None)

        if server_config is None:
            await ctx.send("Server configuration not found.")
            return

        try:
            bmapi = battlemetrics
            await bmapi.setup(server_config['bearer_token'])
            response = await bmapi.ban_list(battlemetrics_server_id)

            if 'data' in response:
                ban_list = response['data']
                response_message = "Ban List:\n"
                for ban in ban_list:
                    reason = ban['attributes'].get('reason', 'No reason provided')
                    response_message += f"- {reason}\n"

                await ctx.send(response_message)
            else:
                await ctx.send("No ban list data found.")
        except Exception as e:
            await ctx.send(f"Error fetching ban list: {e}")
            
    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def clearservers(self, ctx):
        """Clears all server configurations."""
        await self.config.guild(ctx.guild).servers.set([])
        await ctx.send("All server configurations have been cleared.")


    @update_server_info.before_loop
    async def before_update_server_info(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.update_server_info.cancel()

def setup(bot):
    bot.add_cog(BattleMetricsCog(bot))