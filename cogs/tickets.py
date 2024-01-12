import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ticket_channel_id = None

    @commands.command(name="ticketchannel", help="Setup a ticket system in a channel")
    @commands.has_permissions(manage_channels=True)
    async def setup_ticket(self, ctx, channel: nextcord.TextChannel):
        self.ticket_channel_id = channel.id
        button = Button(label="Create Ticket", style=nextcord.ButtonStyle.green)
        button.callback = self.create_ticket_callback
        view = View()
        view.add_item(button)
        embed = nextcord.Embed(title="Ticket System", description="Click the button below to create a new ticket.")
        self.ticket_message = await channel.send(embed=embed, view=view)
        await ctx.send(f"Ticket system set up in {channel.mention}")

    async def create_ticket_callback(self, interaction: nextcord.Interaction):
        member = interaction.user

        thread = await self.ticket_message.create_thread(name=f"ticket-{member.display_name}", auto_archive_duration=60)
        close_button = Button(label="Close Ticket", style=nextcord.ButtonStyle.red)
        close_button.callback = lambda i: self.close_ticket_callback(i, thread)
        view = View()
        view.add_item(close_button)
        embed = nextcord.Embed(title="Your Ticket", description="Support will be with you shortly. Click the button to close this ticket.")
        await thread.send(member.mention, embed=embed, view=view)
        await interaction.response.send_message("Ticket created!", ephemeral=True)

    async def close_ticket_callback(self, interaction: nextcord.Interaction, thread: nextcord.Thread):
        await thread.delete()
        await interaction.response.send_message("Ticket closed.", ephemeral=True)

def setup(bot):
    bot.add_cog(TicketSystem(bot))
