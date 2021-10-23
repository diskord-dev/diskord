import diskord
from diskord.ext import commands

bot = commands.Bot(command_prefix='>')

# these are the list of items that will be 
# shown as choices in autocomplete.
ITEMS = ['Bun', 'Cake', 'Cookie', 'Bread', 'Orange Juice']

# this function would autocomplete the option choices. You can use this
# function to do your processing for example getting some data from 
# a database or from an API but this out of scope of this simple example.

async def autocomplete_items(value: str, interaction: diskord.Interaction):
  if not value:
    # there is a chance user has not entered any value, i.e empty string
    # in which case, we will simply return all the autocomplete items.
    ac_items = [diskord.OptionChoice(name=item, value=item) for item in ITEMS]
  else:
    # in this case, user has input something and we will return
    # the items that start with provided query...
    
    # lowercase the value because case doesn't matter for us and we don't 
    # want autocomplete to break if the value case is not same as items case.
    value = value.lower()
    
    # now return the items whose names start with 
    # the user's entered value. We also lowered case the item name.
    ac_items = [diskord.OptionChoice(name=item, value=item) for item in ITEMS if item.lower().startswith(value)]
  
  # discord API does not allow showing more then 25 choices in autocomplete so we will return
  # the first 25 items otherwise it would raise HTTPException.
  return ac_items[:25]
     

# the command that would autocomplete
# autocomplete function can be specified in `autocomplete` keyword argument. note: autocomplete is only supported
# for string type options.

@bot.slash_command()
@diskord.application.option('item', autocomplete=autocomplete_items)
async def buy(ctx, item: str):
  await ctx.send(f'You bought {item}!')
  
bot.run('token')
