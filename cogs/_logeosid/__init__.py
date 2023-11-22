import json
import nextcord
from nextcord.ext import commands, tasks
from lib.mcrcon import MCRcon
from main import RCON_HOST, RCON_PORT, RCON_PASS

class PlayerIDLogCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logged_players = self.load_player_data()
        self.log_player_ids.start()

    @tasks.loop(seconds=10)
    async def log_player_ids(self):
        await self.bot.wait_until_ready()
        new_player_data = await self.get_player_data()
        self.logged_players.update(new_player_data)
        self.save_player_data()

    async def get_player_data(self):
        try:
            with MCRcon(RCON_HOST, RCON_PASS, RCON_PORT) as mcr:
                response = mcr.command("listplayers")
                player_data = self.extract_player_data(response)
                return player_data
        except Exception as e:
            print(f"Error fetching player data: {e}")
            return {}

    def extract_player_data(self, response):
        # I really hope this works properly.
        lines = response.split("\n")
        player_data = {}
        for line in lines:
            parts = line.split(", ")
            if len(parts) == 2:
                player_name = parts[0].strip()
                player_id = parts[1].strip()
                player_data[player_name] = player_id
        return player_data

    def save_player_data(self):
        with open('data/player_data.json', 'w') as file:
            # Funky way to make data readable.
            json_string = json.dumps(self.logged_players, indent=4)
            file.write(json_string)

    def load_player_data(self):
        try:
            with open('data/player_data.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def cog_unload(self):
        self.log_player_ids.cancel()
        self.save_player_data()

def setup(bot):
    bot.add_cog(PlayerIDLogCog(bot))
