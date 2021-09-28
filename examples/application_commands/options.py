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
@bot.slash_option('text', description='The text to say!')
async def say(ctx, text):
  await ctx.send(f'{ctx.author.name} said: {text}')

# We can do similar for users, roles, channels etc.
@bot.slash_command()
@bot.slash_option('user', description='The user to slap!') 
async def slap(ctx, user: diskord.User): # annotating user as "diskord.User" will make option type a user
  await ctx.send(f'{ctx.author.name} slapped {user.name}')
  
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

