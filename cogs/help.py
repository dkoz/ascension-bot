import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
from settings import BOT_PREFIX

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
            '`/queryserver` - Queries a server for information.\n'
            '`/postserver` - Create a live server tracker in selected channel.\n'
            '`/clearservers` - Clear the live server tracker database.\n',
            inline=False
        )

        embed.add_field(
            name="**Arkon Commands**",
            value='`/arkon rcon` - Send a command to the Ark Server.\n'
            '`/arkon serverchat` - Send a chat message to the Ark Server.\n'
            '`/arkon broadcast` - Send a broadcast to the Ark Server.\n'
            '`/arkon ban` - Ban a player from the Ark server.\n'
            '`/arkon unban` - Unban a player from the Ark server.\n'
            '`/arkon kick` - Kick a player from the Ark Server.\n'
            '`/arkon destroydinos` - Wipe all the wild dinos from the Ark server.\n'
            '`/arkon playerlist` - Display a list of players in the Ark Server.\n'
            '`/arkon getgamelog` - This will fetch the last 600 lines of the servers log file and upload it to discord.\n',
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

    # This will be used to list commands not available as application slash commands.
    # Only administators will be able to use this command.
    @nextcord.slash_command(description="Shows list of available prefix commands", default_member_permissions=nextcord.Permissions(administrator=True))
    async def prefixhelp(self, interaction: nextcord.Interaction):
        bot_avatar_url = self.bot.user.avatar.url
        prefix = BOT_PREFIX

        embed = nextcord.Embed(title="Help Menu", description=f"List of all available commands.", color=nextcord.Color.blue())
        embed.set_footer(text="Created by Koz", icon_url=bot_avatar_url)

        for command in self.bot.commands:
            if not command.hidden and command.enabled:
                embed.add_field(name=f"`{prefix}{command.name}`", value=command.description or "No description", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Please do not remove the about me section. I've worked hard on this bot and this is my only requirement.
    @nextcord.slash_command(description="About Ascension Discord bot for Ark.")
    async def about(self, interaction: nextcord.Interaction):
        bot_avatar_url = self.bot.user.avatar.url

        embed = nextcord.Embed(title="Ascension Bot", color=nextcord.Color.blue())
        embed.set_footer(text="Created by Koz", icon_url=bot_avatar_url)
        embed.add_field(name="About", value="The bot is an open-source project available [here](https://github.com/dkoz/ascension-bot). You can find more info on our readme. I'm always looking for code contributions and support! If there is something wrong with the bot itself, please let me know!", inline=False)
        embed.add_field(name="Creator", value="This bot was created by [Kozejin](https://kozejin.dev). Feel free to add `koz#1337` on discord if you have any questions.", inline=False)

        website_button = Button(label="Website", url="https://kozejin.dev", style=nextcord.ButtonStyle.link)
        github_button = Button(label="Patreon", url="https://www.patreon.com/palbotinn", style=nextcord.ButtonStyle.link)
        project_button = Button(label="Project", url="https://github.com/dkoz/ascension-bot", style=nextcord.ButtonStyle.link)

        view = View()
        view.add_item(website_button)
        view.add_item(github_button)
        view.add_item(project_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

def setup(bot: commands.Bot):
    bot.add_cog(HelpCommand(bot))