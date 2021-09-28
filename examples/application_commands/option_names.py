import diskord
from diskord import commands

bot = commands.Bot(command_prefix='!')

# you can set "arg" keyword argument to the name of argument that represents the option in the command function
# and then change the option name as desired.
@bot.slash_command()
@diskord.slash_option('sentence', arg='text', description='The text to say!')
async def say(ctx, text):
  await ctx.send(f'{ctx.author.name} said: {text}')

# in above command, the option name in discord will appear "sentence" but in this function, it will
# be passed to text argument
  
  
bot.run('token')
