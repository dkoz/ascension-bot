import json
import nextcord
from nextcord.ext import commands
from lib.slash_cooldown import SlashCooldown
import random
from .const import work_scenario
from . import gambling

# Economy cog that needs a lot of work. Feel free to contribute.
class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currency_name = "Points"
        self.user_balances = self.load_balances()
        self.work_scenarios = work_scenario
        self.cooldown = SlashCooldown()
        self.cooldown_seconds = 300

    @nextcord.slash_command(name="balance", description="Check your balance.")
    async def balance(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        balance = self.user_balances.get(user_id, 0)
        embed = nextcord.Embed(title="Balance", description=f"You have {balance} {self.currency_name}.", color=nextcord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="work", description="Work to earn some currency.")
    async def work(self, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)

        if await self.cooldown.apply_cooldown(interaction, user_id, self.cooldown_seconds):
            return

        amount = random.randint(10, 100)
        scenario = random.choice(self.work_scenarios)
        self.user_balances[user_id] = self.user_balances.get(user_id, 0) + amount
        self.save_balances()
        embed = nextcord.Embed(title="Work", description=f"{scenario} You earned {amount} {self.currency_name}.", color=nextcord.Color.green())
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="slots", description="Play slots to win or lose currency.")
    async def slots(self, interaction: nextcord.Interaction, bet: int):
        user_id = str(interaction.user.id)
        if bet > self.user_balances.get(user_id, 0):
            await interaction.response.send_message(embed=nextcord.Embed(description="Insufficient balance to bet.", color=nextcord.Color.red()))
            return

        won, amount, result = gambling.play_slots(bet)
        if won:
            result_msg = f"You won {amount} {self.currency_name}!"
            self.user_balances[user_id] += amount
        else:
            result_msg = f"You lost {bet} {self.currency_name}."
            self.user_balances[user_id] -= bet

        self.save_balances()
        result_str = " | ".join(result)
        embed = nextcord.Embed(title="Slots Result", description=f"{result_str}\n{result_msg}", color=nextcord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="blackjack", description="Play a simulated game of blackjack.")
    async def blackjack(self, interaction: nextcord.Interaction, bet: int):
        user_id = str(interaction.user.id)
        if bet > self.user_balances.get(user_id, 0):
            await interaction.response.send_message(embed=nextcord.Embed(description="Insufficient balance to bet.", color=nextcord.Color.red()))
            return

        outcome, amount, player_score, dealer_score = gambling.play_blackjack(bet)
        if outcome == True:
            result_msg = f"You win with {player_score} points! You won {amount} {self.currency_name}."
            self.user_balances[user_id] += amount
        elif outcome == False:
            result_msg = f"Dealer wins with {dealer_score} points. You lost {bet} {self.currency_name}."
            self.user_balances[user_id] -= bet
        else:
            result_msg = f"It's a draw! Dealer and you both have {player_score} points."

        self.save_balances()
        embed = nextcord.Embed(title="Blackjack Result", description=result_msg, color=nextcord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="transfer", description="Transfer currency to another user.")
    async def transfer(self, interaction: nextcord.Interaction, recipient: nextcord.User, amount: int):
        sender_id = str(interaction.user.id)
        recipient_id = str(recipient.id)

        if sender_id == recipient_id:
            await interaction.response.send_message(embed=nextcord.Embed(description="You cannot transfer currency to yourself.", color=nextcord.Color.red()))
            return

        if self.user_balances.get(sender_id, 0) < amount:
            await interaction.response.send_message(embed=nextcord.Embed(description="Insufficient balance.", color=nextcord.Color.red()))
            return

        self.user_balances[sender_id] = self.user_balances.get(sender_id, 0) - amount
        self.user_balances[recipient_id] = self.user_balances.get(recipient_id, 0) + amount
        self.save_balances()

        embed = nextcord.Embed(title="Transfer", description=f"You transferred {amount} {self.currency_name} to {recipient.mention}.", color=nextcord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @nextcord.slash_command(name="setmoney", description="Set a user's balance.")
    @commands.has_permissions(administrator=True)
    async def set_money(self, interaction: nextcord.Interaction, user: nextcord.User, amount: int):
        user_id = str(user.id)
        self.user_balances[user_id] = amount
        self.save_balances()
        await interaction.response.send_message(embed=nextcord.Embed(title="Balance Updated", description=f"{user.mention}'s balance was set to {amount} {self.currency_name}.", color=nextcord.Color.green()))

    @nextcord.slash_command(name="givemoney", description="Give money to a user.")
    @commands.has_permissions(administrator=True)
    async def give_money(self, interaction: nextcord.Interaction, user: nextcord.User, amount: int):
        user_id = str(user.id)
        self.user_balances[user_id] = self.user_balances.get(user_id, 0) + amount
        self.save_balances()
        await interaction.response.send_message(embed=nextcord.Embed(title="Money Given", description=f"{amount} {self.currency_name} given to {user.mention}.", color=nextcord.Color.green()))

    @nextcord.slash_command(name="removemoney", description="Remove money from a user's balance.")
    @commands.has_permissions(administrator=True)
    async def remove_money(self, interaction: nextcord.Interaction, user: nextcord.User, amount: int):
        user_id = str(user.id)
        self.user_balances[user_id] = max(self.user_balances.get(user_id, 0) - amount, 0)
        self.save_balances()
        await interaction.response.send_message(embed=nextcord.Embed(title="Money Removed", description=f"{amount} {self.currency_name} removed from {user.mention}.", color=nextcord.Color.red()))

    def load_balances(self):
        try:
            with open('data/economy_balances.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_balances(self):
        with open('data/economy_balances.json', 'w') as file:
            json.dump(self.user_balances, file, indent=4)

def setup(bot):
    bot.add_cog(EconomyCog(bot))
