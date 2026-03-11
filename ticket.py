import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput
import io
import os

# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")  # Or hardcode for testing

SERVER_ID = 948971532431015976
OWNER_ID = 458624557763526666

ORDER_CATEGORY_ID = 1481184274249023589
QUEUE_CATEGORY_ID = 1350230717208068228
COMPLETED_CATEGORY_ID = 1481184449247973457
CLOSED_CATEGORY_ID = 1481184543506432032

LOG_CHANNEL_ID = 1481187511769235639
STAFF_ROLE_ID = 1481186627790307431

BLUE = discord.Color.from_rgb(135, 206, 250)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- HELPERS ----------------
def is_staff(member):
    return any(role.id == STAFF_ROLE_ID for role in member.roles)

async def transcript(channel):
    messages = []
    async for msg in channel.history(limit=None, oldest_first=True):
        messages.append(f"{msg.author}: {msg.content}")
    data = "\n".join(messages)
    return io.BytesIO(data.encode())

def ticket_exists(guild, user, prefix):
    return any(ch.name == f"{prefix}-{user.name}".lower() for ch in guild.text_channels)

# ---------------- MODALS ----------------
class OrderModal(Modal, title="📦 Order Form"):
    product = TextInput(label="Product / Service")
    quantity = TextInput(label="Quantity")
    payment = TextInput(label="Payment Method")
    notes = TextInput(label="Extra Notes", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        if ticket_exists(interaction.guild, interaction.user, "order"):
            await interaction.response.send_message("⚠ You already have an open order ticket.", ephemeral=True)
            return

        category = interaction.guild.get_channel(ORDER_CATEGORY_ID)
        channel = await interaction.guild.create_text_channel(
            name=f"order-{interaction.user.name}".lower(),
            category=category
        )

        embed = discord.Embed(title="📦 New Order", color=BLUE)
        embed.add_field(name="Product", value=self.product)
        embed.add_field(name="Quantity", value=self.quantity)
        embed.add_field(name="Payment", value=self.payment)
        embed.add_field(name="Notes", value=self.notes)

        await channel.send(f"{interaction.user.mention}", embed=embed, view=TicketButtons())
        await interaction.response.send_message(f"✅ Your order ticket has been created: {channel.mention}", ephemeral=True)

class ReportModal(Modal, title="⚠ Report Product"):
    product = TextInput(label="Product Name")
    issue = TextInput(label="What happened?")
    details = TextInput(label="Product details")
    time = TextInput(label="When did you buy it?")

    async def on_submit(self, interaction: discord.Interaction):
        if ticket_exists(interaction.guild, interaction.user, "report"):
            await interaction.response.send_message("⚠ You already have an open report ticket.", ephemeral=True)
            return

        category = interaction.guild.get_channel(ORDER_CATEGORY_ID)
        channel = await interaction.guild.create_text_channel(
            name=f"report-{interaction.user.name}".lower(),
            category=category
        )

        embed = discord.Embed(title="⚠ Product Report", color=BLUE)
        embed.add_field(name="Product", value=self.product)
        embed.add_field(name="Issue", value=self.issue)
        embed.add_field(name="Details", value=self.details)
        embed.add_field(name="Purchased", value=self.time)

        await channel.send(f"{interaction.user.mention}", embed=embed, view=TicketButtons())
        await interaction.response.send_message(f"✅ Your report ticket has been created: {channel.mention}", ephemeral=True)

# ---------------- VIEWS ----------------
class TicketButtons(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.primary)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return
        category = interaction.guild.get_channel(QUEUE_CATEGORY_ID)
        await interaction.channel.edit(category=category)
        await interaction.response.send_message("📥 Ticket moved to queue.")

    @discord.ui.button(label="Completed", style=discord.ButtonStyle.success)
    async def complete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return
        category = interaction.guild.get_channel(COMPLETED_CATEGORY_ID)
        await interaction.channel.edit(category=category)
        await interaction.response.send_message("✅ Ticket marked completed.")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return
        file = await transcript(interaction.channel)
        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(f"📄 Transcript for {interaction.channel.name}", file=discord.File(file, filename="transcript.txt"))
        category = interaction.guild.get_channel(CLOSED_CATEGORY_ID)
        await interaction.channel.edit(category=category)
        await interaction.response.send_message("🔒 Ticket closed.")

class TicketDropdown(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="☁ Choose ticket type...",
        options=[
            discord.SelectOption(label="Create Order", emoji="📦"),
            discord.SelectOption(label="Report Product", emoji="⚠"),
        ]
    )
    async def dropdown(self, interaction: discord.Interaction, select: Select):
        if select.values[0] == "Create Order":
            await interaction.response.send_modal(OrderModal())
        elif select.values[0] == "Report Product":
            await interaction.response.send_modal(ReportModal())

# ---------------- COMMANDS ----------------
@bot.command()
async def panel(ctx):
    embed = discord.Embed(title="☁ Pocoyo Ticket System", description="Select a ticket option below to continue.", color=BLUE)
    await ctx.send(embed=embed, view=TicketDropdown())

# ---------------- READY ----------------
@bot.event
async def on_ready():
    bot.add_view(TicketDropdown())
    bot.add_view(TicketButtons())
    print(f"✅ Bot Ready: {bot.user}")

# ---------------- RUN ----------------
if not TOKEN:
    print("TOKEN not found in environment variables")
    exit()

bot.run(TOKEN)
