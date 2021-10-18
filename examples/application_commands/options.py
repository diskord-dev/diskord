import diskord
from diskord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
  print('ready')

# this example will go through the process of creating options in a slash command.
# Bot.slash_option decorator can be used to make options.
@bot.slash_command()
# the first argument "text" is the name of option and the name of argument
# in command function that represents this option.
@diskord.application.option('text', description='The text to say!')
async def say(ctx, text):
  await ctx.respond(f'{ctx.author.name} said: {text}')

# We can do similar for users, roles, channels etc.
@diskord.slash_command()
@diskord.application.option('user', description='The user to slap!')
@diskord.application.option('amount', description='Amounts of slaps! Defaults to 1')
# annotating user as "diskord.User" will make option type a user and same for "int"
# setting a default value to an argument will make that option optional.
async def slap(ctx, user: diskord.User, amount: int = 1):
  await ctx.respond(f'{ctx.author.name} slapped {user.name}, {amount} times!')

# available types are:
# diskord.Role: For role
# diskord.abc.GuildChannel: for channels
# diskord.Member or diskord.User: for users
# typing.Union[diskord.Member, diskord.Role]: Any mentionable i.e user or role
# int: for integers
# float: for numbers
# str: for strings
# bool: for booleans
bot.run('token')

