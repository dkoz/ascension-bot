import nextcord
from nextcord.ext import commands
from config import whitelist

class UtilitiesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_whitelisted(self, guild_id):
        return guild_id in whitelist

    async def leave_non_whitelisted_guilds(self):
        for guild in self.bot.guilds:
            if not self.is_whitelisted(guild.id):
                await guild.leave()
                print(f"Left guild: {guild.name} (ID: {guild.id})")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot is connected and ready. Whitelist check will be performed.")
        await self.leave_non_whitelisted_guilds()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        if not self.is_whitelisted(guild.id):
            await guild.leave()
            print(f"Left guild: {guild.name} (ID: {guild.id})")

    @commands.command(description="Get a list of guilds the bot is connected to.")
    @commands.is_owner()
    async def guilds(self, ctx):
        embed = nextcord.Embed(title="Connected Guilds", color=0x00ff00)
        for guild in self.bot.guilds:
            embed.add_field(name=guild.name, value=f"ID: {guild.id}", inline=False)

        await ctx.send(embed=embed)

    @guilds.error
    async def guilds_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("This command is restricted to the bot owner.")

def setup(bot):
    bot.add_cog(UtilitiesCog(bot))