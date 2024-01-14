import asyncio
import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import has_permissions
import logging

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            original = error.original
            if isinstance(original, nextcord.HTTPException):
                await ctx.send("An HTTP error occurred: " + str(original))
            elif isinstance(original, nextcord.Forbidden):
                await ctx.send("I do not have permission to do that.")
            else:
                logging.error(f"An error occurred: {original}")
                await ctx.send("An unexpected error occurred. Please contact the bot administrator.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have the required permissions to use this command.")

    @commands.group(name="embed", aliases=["sk"], invoke_without_command=True)
    async def embed_group(self, ctx):
        prefix = ctx.prefix

        embed = nextcord.Embed(
            title="Embed System",
            description=f"`{prefix}embed say` - Send a message as the bot\n"
                        f"`{prefix}embed embed` - Send an embedded message as the bot\n"
                        f"`{prefix}embed edit` - Edit a message sent by the bot\n"
                        f"`{prefix}embed editembed` - Edit an embedded message sent by the bot\n"
                        f"`{prefix}embed addbutton` - Add a button to an embedded message sent by the bot",
            color=nextcord.Color.orange()
        )
        await ctx.send(embed=embed)

    @embed_group.command(name="say")
    @has_permissions(manage_messages=True)
    async def speak_say(self, ctx, destination: nextcord.TextChannel, *, content):
        if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.send("I do not have permission to delete messages in this channel.")
            return

        if not destination.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"I do not have permission to send messages in {destination.mention}.")
            return

        try:
            await ctx.message.delete()
            await destination.send(content=content)
        except nextcord.Forbidden:
            await ctx.send("I'm missing permissions to complete this action.")

    @embed_group.command(name="embed")
    @has_permissions(manage_messages=True)
    async def speak_embed(self, ctx, destination: nextcord.TextChannel):
        """Create an embedded message as the bot with additional options."""
        if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.send("I do not have permission to delete messages in this channel.")
            return
        
        embed = await self.create_or_edit_embed(ctx)
        await destination.send(embed=embed)

    @embed_group.command(name="edit")
    @has_permissions(manage_messages=True)
    async def speak_edit(self, ctx, channel: nextcord.TextChannel, message_id: int, *, new_content):
        """Edit a message sent by the bot."""
        try:
            message = await channel.fetch_message(message_id)
        except nextcord.NotFound:
            await ctx.send("Could not find the specified message.")
            return

        if message.author != self.bot.user:
            await ctx.send("You can only edit messages sent by the bot.")
            return

        if message.embeds:
            await ctx.send("This command only works for non-embedded messages. Use 'editembed' for embedded messages.")
        else:
            await self.edit_message(ctx, message, new_content)

    @embed_group.command(name="editembed")
    @has_permissions(manage_messages=True)
    async def speak_edit_embed(self, ctx, channel: nextcord.TextChannel, message_id: int):
        """Edit the embedded message sent by the bot with additional options."""
        try:
            message = await channel.fetch_message(message_id)
        except nextcord.NotFound:
            await ctx.send("Could not find the specified message.")
            return

        if message.author != self.bot.user:
            await ctx.send("You can only edit messages sent by the bot.")
            return

        if message.embeds:
            old_embed = message.embeds[0]
            new_embed = await self.create_or_edit_embed(ctx, old_embed)
            await message.edit(embed=new_embed)
            await ctx.send("Embedded message edited.")
        else:
            await ctx.send("The specified message does not have an embed.")

    async def edit_message(self, ctx, message: nextcord.Message, new_content: str):
        await message.edit(content=new_content)
        await ctx.send("Message edited.")

    async def create_or_edit_embed(self, ctx, embed=None):
        if embed is None:
            embed = nextcord.Embed()

        current_title = embed.title if embed.title else "No title set"
        await ctx.send(f"Current title: {current_title}\nPlease enter the new title (or type 'skip' to keep the current one):")
        try:
            title = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
            if title.content.lower() != 'skip':
                embed.title = title.content
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out. Please try again.")
            return

        current_description = embed.description if embed.description else "No description set"
        await ctx.send(f"Current description: {current_description}\nPlease enter the new description (or type 'skip' to keep the current one):")
        try:
            description = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
            if description.content.lower() != 'skip':
                embed.description = description.content
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out. Please try again.")
            return
        
        current_thumbnail = embed.thumbnail.url if embed.thumbnail else "No thumbnail set"
        await ctx.send(f"Current thumbnail URL: {current_thumbnail}\nPlease enter the new thumbnail URL (or type 'skip' to keep the current one):")
        try:
            thumbnail_url = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
            if thumbnail_url.content.lower() != 'skip':
                embed.set_thumbnail(url=thumbnail_url.content)
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out. Please try again.")
            return

        current_image = embed.image.url if embed.image else "No image set"
        await ctx.send(f"Current image URL: {current_image}\nPlease enter the new image URL (or type 'skip' to keep the current one):")
        try:
            image_url = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
            if image_url.content.lower() != 'skip':
                embed.set_image(url=image_url.content)
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out. Please try again.")
            return

        for i, field in enumerate(list(embed.fields)):
            await ctx.send(f"Field {i+1} - Name: {field.name}\nValue: {field.value}\nInline: {field.inline}\nType 'edit' to edit this field, 'delete' to remove it, or 'skip' to keep it as is.")
            try:
                response = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                if response.content.lower() == 'edit':
                    await ctx.send("Enter the new name for the field:")
                    new_name = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                    await ctx.send("Enter the new value for the field:")
                    new_value = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                    await ctx.send("Should this field be inline? (yes/no):")
                    new_inline = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                    embed.set_field_at(i, name=new_name.content, value=new_value.content, inline=new_inline.content.lower() == 'yes')
                elif response.content.lower() == 'delete':
                    embed.remove_field(i)
            except asyncio.TimeoutError:
                await ctx.send("Operation timed out. Please try again.")
                return

        await ctx.send("How many additional fields do you want to add? (Enter a number or type '0' to skip):")
        try:
            num_fields = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
            for _ in range(int(num_fields.content)):
                await ctx.send("Enter the name of the field:")
                field_name = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                await ctx.send("Enter the value of the field:")
                field_value = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                await ctx.send("Should this field be inline? (yes/no):")
                field_inline = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                embed.add_field(name=field_name.content, value=field_value.content, inline=field_inline.content.lower() == 'yes')
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out. Please try again.")
            return

        return embed

    @embed_group.command(name="addbutton")
    @has_permissions(manage_messages=True)
    async def speak_add_button(self, ctx, channel: nextcord.TextChannel, message_id: int):
        try:
            message = await channel.fetch_message(message_id)
        except nextcord.NotFound:
            await ctx.send("Could not find the specified message.")
            return
        except nextcord.HTTPException as e:
            await ctx.send(f"An HTTP error occurred: {e}")
            return

        if message.author != self.bot.user or not message.embeds:
            await ctx.send("You can only add buttons to embedded messages sent by the bot.")
            return

        old_embed = message.embeds[0]
        new_embed = nextcord.Embed.from_dict(old_embed.to_dict())

        view = nextcord.ui.View()

        try:
            await ctx.send("Please enter the number of buttons you want to add:")
            num_buttons = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
            num_buttons = int(num_buttons.content)

            for i in range(num_buttons):
                await ctx.send(f"Please enter the label for button {i+1}:")
                button_label = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
                await ctx.send(f"Please enter the URL for button {i+1}:")
                button_url = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)

                if not button_url.content.startswith(('http://', 'https://', 'discord://')):
                    await ctx.send(f"Invalid URL for button {i+1}. Please make sure the URL starts with 'http', 'https', or 'discord'.")
                    continue

                class LinkButton(nextcord.ui.Button):
                    def __init__(self):
                        super().__init__(label=button_label.content, style=nextcord.ButtonStyle.link, url=button_url.content)

                link_button = LinkButton()
                view.add_item(link_button)

            await message.edit(embed=new_embed, view=view)
            await ctx.send("Buttons added to embedded message.")
        except asyncio.TimeoutError:
            await ctx.send("Operation timed out. Please try again.")
        except ValueError:
            await ctx.send("Invalid number of buttons. Please enter a valid number.")
        except nextcord.HTTPException as e:
            await ctx.send(f"An HTTP error occurred: {e}")

def setup(bot):
    bot.add_cog(EmbedCog(bot))