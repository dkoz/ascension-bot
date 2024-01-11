import nextcord
from nextcord.ext import commands, tasks
from lib.arkon_async import ArkonClient
import asyncio
import os
import json

class LogEOSIDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.logged_players = self.load_player_data()
        self.log_player_ids.start()
        self.rcon_cooldown = 320

    def load_config(self):
        config_path = os.path.join('data', 'config.json')
        with open(config_path) as config_file:
            config = json.load(config_file)
            self.servers = config["RCON_SERVERS"]

    @tasks.loop(seconds=10)
    async def log_player_ids(self):
        await self.bot.wait_until_ready()
        for server_name in self.servers:
            new_player_data = await self.get_player_data(server_name)
            for player_name, player_id in new_player_data.items():
                if player_id not in self.logged_players.values():
                    self.logged_players[player_name] = player_id
            self.save_player_data()

    async def get_player_data(self, server_name):
        server = self.servers[server_name]
        try:
            async with ArkonClient(server["RCON_HOST"], server["RCON_PORT"], server["RCON_PASS"]) as ac:
                response = await ac.send("listplayers")
                player_data = self.extract_player_data(response)
                return player_data
        except Exception as e:
            print(f"Error fetching player data from {server_name}: {e}")
            await asyncio.sleep(self.rcon_cooldown)
            return {}

    def extract_player_data(self, response):
        lines = response.split("\n")
        player_data = {}
        for line in lines:
            parts = line.split(", ")
            if len(parts) == 2:
                player_name = parts[0].split()[-1].strip()
                player_id = parts[1].strip()
                player_data[player_name] = player_id
        return player_data

    def save_player_data(self):
        directory = 'data'
        filepath = os.path.join(directory, 'player_data.json')

        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(filepath, 'w') as file:
            json_string = json.dumps(self.logged_players, indent=4)
            file.write(json_string)

    def load_player_data(self):
        directory = 'data'
        filepath = os.path.join(directory, 'player_data.json')

        if not os.path.exists(directory):
            os.makedirs(directory)

        try:
            with open(filepath, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def cog_unload(self):
        self.log_player_ids.cancel()
        self.save_player_data()

def setup(bot):
    bot.add_cog(LogEOSIDCog(bot))
