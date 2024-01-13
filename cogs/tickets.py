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
        self.bot.loop.create_task(self.setup_buttons())

    def load_config(self):
        if not os.path.exists(self.config_file):
            os.makedirs(self.data_folder, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({'ticket_channel_id': None, 'log_channel_id': None, 'buttons': []}, f)
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f)

    async def setup_buttons(self):
        await self.bot.wait_until_ready()
        if 'buttons' in self.data:
            for button_info in self.data['buttons']:
                channel = self.bot.get_channel(button_info['channel_id'])
                if channel:
                    try:
                        message = await channel.fetch_message(button_info['message_id'])
                    except (nextcord.NotFound, nextcord.HTTPException):
                        continue

                    view = View()
                    button = Button(label=button_info['label'], style=nextcord.ButtonStyle(button_info['style']), custom_id=button_info['custom_id'])
                    button.callback = self.button_callback
                    view.add_item(button)
                    await message.edit(view=view)

    @commands.group(name="tickets", invoke_without_command=True)
    async def tickets(self, ctx):
        prefix = ctx.prefix

        embed = nextcord.Embed(
            title="Ticket System",
            description=f"{prefix}tickets channel - Set the ticket channel\n"
                        f"{prefix}tickets logchannel - Set the log channel."
        )
        await ctx.send(embed=embed)

    @tickets.command(name="channel")
    async def setup_ticket(self, ctx, channel: nextcord.TextChannel):
        self.data['ticket_channel_id'] = channel.id
        self.save_config()
        button = Button(label="Create Ticket", style=nextcord.ButtonStyle.green, custom_id="create_ticket")
        button.callback = self.button_callback
        view = View()
        view.add_item(button)
        embed = nextcord.Embed(title="Ticket System", description="Click the button below to create a new ticket.")
        message = await channel.send(embed=embed, view=view)
        # Save button state
        self.data['buttons'].append({
            'channel_id': channel.id,
            'message_id': message.id,
            'label': button.label,
            'style': button.style.value,
            'custom_id': button.custom_id
        })
        self.save_config()
        await ctx.send(f"Ticket system set up in {channel.mention}")

    @tickets.command(name="logchannel")
    async def setup_log(self, ctx, channel: nextcord.TextChannel):
        self.data['log_channel_id'] = channel.id
        self.save_config()
        await ctx.send(f"Ticket log channel set to {channel.mention}")

    async def button_callback(self, interaction: nextcord.Interaction):
        custom_id = interaction.data.get('custom_id')
        if custom_id == "create_ticket":
            await self.create_ticket(interaction)
        elif custom_id.startswith("close_ticket_"):
            thread_id = int(custom_id.split("_")[-1])
            thread = await self.bot.fetch_channel(thread_id)
            await self.close_ticket(interaction, thread)

    async def create_ticket(self, interaction: nextcord.Interaction):
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

            close_button = Button(label="Close Ticket", style=nextcord.ButtonStyle.red, custom_id=f"close_ticket_{thread.id}")
            close_button.callback = self.button_callback
            view = View()
            view.add_item(close_button)
            embed = nextcord.Embed(title="Your Ticket", description="Support will be with you shortly. Click the button to close this ticket.")
            message = await thread.send(member.mention, embed=embed, view=view)
            await interaction.response.send_message("Ticket created!", ephemeral=True)

            self.data['buttons'].append({
                'channel_id': thread.id,
                'message_id': message.id,
                'label': close_button.label,
                'style': close_button.style.value,
                'custom_id': close_button.custom_id
            })
            self.save_config()

    async def close_ticket(self, interaction: nextcord.Interaction, thread: nextcord.Thread):
        member = interaction.user
        parent_channel = thread.parent

        overwrites = parent_channel.overwrites_for(member)
        overwrites.send_messages = False
        overwrites.read_messages = False
        await parent_channel.set_permissions(member, overwrite=overwrites, reason="Ticket closed")

        closing_embed = nextcord.Embed(title="Closed", description="Your ticket has been closed.", color=nextcord.Color.red())
        await interaction.response.send_message(embed=closing_embed)

        await thread.edit(archived=True, locked=True)

        self.data['buttons'] = [button for button in self.data['buttons'] if button['message_id'] != thread.last_message_id]
        self.save_config()

def setup(bot):
    bot.add_cog(TicketSystem(bot))
