import diskord
from diskord.ext import commands

bot = commands.Bot(command_prefix='>')

# This example showcases the way of showing dynamic choices depending on the value
# that the user passes in previous option.

async def autocomplete(value: str, option: diskord.application.Option, interaction: diskord.Interaction):
    # "option" is the currently focused option.
    # as such, we will check if the focused option name is color,
    # if it is, we would simply return all the color names.
    if option.name == 'color':
        items = ['brown', 'green', 'blue']

    # if the focused option isn't color and is "organism" instead, this means
    # the user has specified a color and now we have to return the list
    # of organisms of that color.

    elif option.name == 'organism':
        # interaction.data is the raw data of interaction and
        # we are accessing "options" which is list of options that is being
        # specified by user. The first element here is the "color" option and we
        # are accessing it's value.
        color = interaction.data['options'][0]['value']

        # now "color" is the value that user specified for color option.
        # let's now return the names depending on value.
        if color == 'brown':
            items = ['Bear', 'Dog', 'Donkey']
        elif color == 'green':
            items = ['Snake', 'Grasshopper', 'Frog']
        elif color == 'blue':
            items = ['Whale', 'Jelly fish', 'Alien']

    # finally return the choices.
    return [diskord.OptionChoice(name=item, value=item) for item in items]


# the actual command
@bot.slash_command()
@diskord.application.option('color', autocomplete=autocomplete)
@diskord.application.option('organism', autocomplete=autocomplete)
async def organism(ctx, color: str, organism: str):
    await ctx.send(f'A {color} colored {organism}.')
