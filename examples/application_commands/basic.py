import diskord
from diskord.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
  print('ready')

# slash commands can be used by writing "/<command>" in the chat
@bot.slash_command()
async def ping(ctx):
  await ctx.respond('pong')

# message commands can be used by right clicking a user > apps > command  
@bot.user_command()
async def slap(ctx, user):
  await ctx.respond(f'{ctx.author.name} slapped {user.name}')

# message commands can be used by right clicking a message > apps > command
@bot.message_command()
async def say(ctx, message):
  await ctx.respond(f'{ctx.author.name} requested to say: {message.content}')

bot.run('token')
