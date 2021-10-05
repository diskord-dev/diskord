import diskord
from diskord.ext import commands

bot = commands.Bot(command_prefix='!')

# want to nest subcommands and groups in slash commands? you can do that!

# note: once you define subcommands and groups your top command or the parent command is not valid as it is i.e you
# can't do "/top" but you have to specify the subcommand.
@bot.slash_command()
async def top(ctx):
  pass

@top.sub_command()
async def sub(ctx):
  await ctx.respond('a subcommand!')

# the usage would be "/top sub"

# you can also make command groups

@bot.slash_command()
async def grouptop(ctx):
  pass

@grouptop.sub_command_group()
async def group(ctx):
  pass

@group.sub_command(ctx)
async def groupcmd(ctx):
  await ctx.respond('i am in a group!')
  
# the usage would be /grouptop group groupcmd
bot.run('token')
