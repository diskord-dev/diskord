import diskord
from diskord.ext import commands

bot = commands.Bot(command_prefix='>')


# minimum values and maximum values can be set on an integer or number (float) 
# option types using `min_value` and `max_value` keyword arguments in `option()`

# in the command below, the "quantity" option cannot be lower then "1" and higher then "10"
@bot.slash_command(name='buy-cookies')
@bot.application.option('quantity', min_value=1, max_value=10, description='The quantity of cookies to buy. Can be higher then 0 and max 10.')
async def buy_cookies(ctx, quantity: int):
  await ctx.send(f'You bought {quantity} cookies.')

bot.run('token')
