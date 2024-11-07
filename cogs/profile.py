import nextcord
from nextcord.ext import commands
import os
import json

class LinkAccountCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.linked_accounts = self.load_linked_accounts()
        self.player_data = self.load_player_data()

    @nextcord.slash_command(description="Link your Discord account with your EOS ID.")
    async def link(self, interaction: nextcord.Interaction, eos_id: str = None):
        if not eos_id:
            await interaction.response.send_message("Please provide your EOS ID.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        self.linked_accounts[user_id] = {"eos_id": eos_id}

        self.save_linked_accounts()
        await interaction.response.send_message("Your EOS ID has been linked!", ephemeral=True)

    # Just for the sake of GDPR
    @nextcord.slash_command(description="Erase your linked EOS ID.")
    async def unlink(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        if user_id in self.linked_accounts:
            del self.linked_accounts[user_id]
            self.save_linked_accounts()
            await interaction.response.send_message("Your linked profile has been erased.", ephemeral=True)
        else:
            await interaction.response.send_message("You do not have a linked profile.", ephemeral=True)

    @nextcord.slash_command(description="Display your linked EOS ID.")
    async def me(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        if user_id in self.linked_accounts:
            account_info = self.linked_accounts[user_id]
            embed = nextcord.Embed(title=f"{interaction.user.name}'s Profile", color=nextcord.Color.blue())
            embed.set_thumbnail(url=interaction.user.avatar.url)
            embed.add_field(name="Discord Name", value=interaction.user.name, inline=False)

            if "eos_id" in account_info:
                embed.add_field(name="EOS ID", value=account_info["eos_id"], inline=False)

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("You have not linked any IDs.", ephemeral=True)

    @nextcord.slash_command(description="Find a player's EOS ID by their name.")
    async def find(self, interaction: nextcord.Interaction, player_name: str):
        full_name, eos_id = self.find_player_id(player_name)
        if eos_id:
            await interaction.response.send_message(f"EOS ID for {full_name}: {eos_id}")
        else:
            await interaction.response.send_message(f"No EOS ID found for {player_name}.", ephemeral=True)

    @find.on_autocomplete("player_name")
    async def autocomplete_player_name(self, interaction: nextcord.Interaction, option_value: str):
        if not option_value:
            return []

        player_data = self.load_player_data()

        search_term = option_value.lower()
        matching_names = []
        for name in player_data.keys():
            if search_term in name.lower():
                matching_names.append(name)

        matching_names = matching_names[:25]

        await interaction.response.send_autocomplete(matching_names)

    def find_player_id(self, player_name):
        player_name = player_name.strip()
        if player_name in self.player_data:
            return player_name, self.player_data[player_name]
        return None, None

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

    def save_linked_accounts(self):
        directory = 'data'
        filepath = os.path.join(directory, 'linked_accounts.json')

        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(filepath, 'w') as file:
            json.dump(self.linked_accounts, file, indent=4)

    def load_linked_accounts(self):
        directory = 'data'
        filepath = os.path.join(directory, 'linked_accounts.json')

        if not os.path.exists(directory):
            os.makedirs(directory)

        try:
            with open(filepath, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def cog_unload(self):
        self.save_linked_accounts()

def setup(bot):
    cog = LinkAccountCog(bot)
    bot.add_cog(cog)
    if not hasattr(bot, 'all_slash_commands'):
        bot.all_slash_commands = []
    bot.all_slash_commands.extend([
        cog.link,
        cog.unlink,
        cog.me,
        cog.find
    ])
