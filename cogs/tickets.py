import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View
import json
import os

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_folder = 'data'
        self.config_file = os.path.join(self.data_folder, 'tickets.json')
        self.data = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            os.makedirs(self.data_folder, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({'ticket_channel_id': None, 'log_channel_id': None}, f)
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f)

    @commands.group(name="tickets", help="Ticket system commands", invoke_without_command=True)
    async def tickets(self, ctx):
        embed = nextcord.Embed(title="Ticket System", description="Use the commands below to set up the ticket system.")
        embed.add_field(name="Setup", value=f"`{ctx.prefix}ticket channel <channel>`\n`{ctx.prefix}ticket logchannel <channel>`")
        await ctx.send(embed=embed)

    @tickets.command(name="channel", help="Setup a ticket system in a channel")
    async def setup_ticket(self, ctx, channel: nextcord.TextChannel):
        self.data['ticket_channel_id'] = channel.id
        self.save_config()
        button = Button(label="Create Ticket", style=nextcord.ButtonStyle.green)
        button.callback = self.create_ticket_callback
        view = View()
        view.add_item(button)
        embed = nextcord.Embed(title="Ticket System", description="Click the button below to create a new ticket.")
        await channel.send(embed=embed, view=view)
        await ctx.send(f"Ticket system set up in {channel.mention}")

    @tickets.command(name="logchannel", help="Set the channel to send ticket logs to")
    async def setup_log(self, ctx, channel: nextcord.TextChannel):
        self.data['log_channel_id'] = channel.id
        self.save_config()
        await ctx.send(f"Ticket logs will be sent to {channel.mention}")

    async def create_ticket_callback(self, interaction: nextcord.Interaction):
        member = interaction.user
        ticket_channel_id = self.data.get('ticket_channel_id')
        if ticket_channel_id:
            ticket_channel = self.bot.get_channel(ticket_channel_id)
            thread = await ticket_channel.create_thread(name=f"ticket-{member.display_name}", auto_archive_duration=60)

            if self.data.get('log_channel_id'):
                log_channel = self.bot.get_channel(self.data['log_channel_id'])
                if log_channel:
                    embed = nextcord.Embed(title="Ticket Opened", color=nextcord.Color.green())
                    embed.set_thumbnail(url=member.avatar.url)
                    embed.add_field(name="Created By", value=f"{member.display_name}\n{member.mention}", inline=False)
                    embed.add_field(name="User ID", value=member.id, inline=False)
                    embed.add_field(name="Opened", value=interaction.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
                    embed.add_field(name="Ticket Name", value=thread.name, inline=False)
                    view = View()
                    view.add_item(Button(label="Go to Ticket", style=nextcord.ButtonStyle.link, url=thread.jump_url))
                    await log_channel.send(embed=embed, view=view)

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
