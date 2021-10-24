import diskord
from diskord.ext import commands

client=commands.Bot(command_prefix="d!", intents=diskord.Intents.all())
client.remove_command("help")

class HelpDropdown(diskord.ui.Select):
    def __init__(self):

        options=[
            diskord.SelectOption(label="Utilities", description="See all the utilities commands", emoji="🧰"),
            diskord.SelectOption(label="Moderation", description="See al the moderation commands", emoji="🔨"),
            diskord.SelectOption(label="Miscellaneous", description="See all the miscellaneous commands", emoji="📌"),
            diskord.SelectOption(label="Images", description="See all the images commands", emoji="🖼️")
        ]

        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: diskord.Interaction):

        msg = interaction.message

        if self.values[0] == "Utilities":
            # await interaction.response.send_message(f'You selected {self.values[0]}')
            await msg.edit(content="You selected utilities")
        if self.values[0] == "Moderation":
            await msg.edit(content="You selected moderation")
        if self.values[0] == "Miscellaneous":
            await msg.edit(content="You selected miscellaneous")
        if self.values[0] == "Images":
            await msg.edit(content="You selected images")

class HelpDropdownView(diskord.ui.View):
    def __init__(self):
        super().__init__()

        self.add_item(HelpDropdown())

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")

@client.command()
async def help(ctx):
    view=HelpDropdownView()

    await ctx.send("Select a category.", view=view)

client.run("bot-token")
