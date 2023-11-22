import nextcord
from nextcord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="Shows a list of available commands")
    async def help(self, interaction: nextcord.Interaction):
        bot_avatar_url = self.bot.user.avatar.url

        embed = nextcord.Embed(title="Help Menu", description="List of commands for Ark Dev Bot", color=nextcord.Color.blue())
        embed.set_footer(text="Created by Koz", icon_url=bot_avatar_url)

        embed.add_field(
            name="**Commands**",
            value='`/help` - Show the help menu you are looking at now.\n'
            '`/about` - Information about the bot.\n'
            '`/serverstatus` - Displays the status of the server.\n'
            '`/rcon command` - Send a command to the Ark Server.\n'
            '`/rcon serverchat` - Send a chat message to the Ark Server.',
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(description="About my bot")
    async def about(self, interaction: nextcord.Interaction):
        bot_avatar_url = self.bot.user.avatar.url

        embed = nextcord.Embed(title="Ark Dev Bot", color=nextcord.Color.blue())
        embed.set_footer(text="Created by Koz", icon_url=bot_avatar_url)
        embed.add_field(name="About", value="Still in development", inline=False)
        embed.add_field(name="Creator", value="This bot was created by `koz` on Discord. Feel free to add me if you have any questions.", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(HelpCommand(bot))