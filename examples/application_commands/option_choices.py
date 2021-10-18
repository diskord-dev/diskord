import diskord
from diskord.ext import commands

bot = commands.Bot(command_prefix='!')

# you can add certain choices to an option by passing in choices kwarg in slash_option decorator!
@bot.slash_command()
@bot.application.option('item', description='The item to buy.', choices=[
    # the name is represents the name of choice that is displayed in discord and value is what is passed in command function
    diskord.OptionChoice(name='Cake', value='cake'),
    diskord.OptionChoice(name='Cookie', value='cookie'),
    diskord.OptionChoice(name='Candy', value='candy'),
])
@diskord.application.option('quantity', description='The quantity of items to buy. Defaults to 1')
async def buy(ctx, item, quantity: int = 1):
  await ctx.respond(f'you bought {quantity} {item}(s)!')

bot.run('token')
