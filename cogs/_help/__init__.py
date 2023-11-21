import nextcord
from nextcord.ext import commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(description="Shows a list of available commands~")
    async def help(self, ctx):
        bot_avatar_url = self.bot.user.avatar.url

        embed = nextcord.Embed(title="Help Menu", description="List of commands for Ark Dev Bot", color=nextcord.Color.blue())
        embed.set_footer(text="Created by Koz", icon_url=bot_avatar_url)
        embed.add_field(name="`/about`", value="Shows information about the bot.", inline=False)
        embed.add_field(name="↳ Other commands?", value="More commands will be added soon.", inline=False)
        embed.add_field(name="`/addserver`", value="Not working yet", inline=False)
        await ctx.send(embed=embed)

    @nextcord.slash_command(description="About my bot~")
    async def about(self, ctx):
        bot_avatar_url = self.bot.user.avatar.url

        embed = nextcord.Embed(title="Ark Dev Bot", color=nextcord.Color.blue())
        embed.set_footer(text="Created by Koz", icon_url=bot_avatar_url)
        embed.add_field(name="About", value="Still in development", inline=False)
        embed.add_field(name="Creator", value="This bot was created by `koz` on Discord. Feel free to add me if you have any questions.", inline=False)

        await ctx.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(HelpCommand(bot))
