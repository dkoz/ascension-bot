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
            name="**Default Commands**",
            value='`/help` - Show the help menu you are looking at now.\n'
            '`/about` - Information about the bot.\n'
            '`/queryserver` - Queries a server for information.\n'
            '`/postserver` - Create a live server tracker in selected channel.\n'
            '`/arkon command` - Send a command to the Ark Server.\n'
            '`/arkon serverchat` - Send a chat message to the Ark Server.\n',
            inline=False
        )

        embed.add_field(
            name="**Profile Commands**",
            value='`/link` - Link your `SteamID` or `EOS ID` to the bot. \n'
            '`/me` - Shows you profile with link information.\n'
            '`/unlink` - Remove your data from the bot.\n'
            '`/find` - Search the bots database for your `EOS ID`',
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