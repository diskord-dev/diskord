"""

THIS COMMAND USES THE MASTER BRANCH VERSION! 
Uninstall the 2.6.2 version with "pip uninstall diskord" and install the new version with "pip install git+https://github.com/diskord-dev/diskord"

"""

import diskord
from diskord.ext import commands
import humanfriendly # <-- library for converting time (do "pip install humanfriendly" in your terminal)
import datetime

client = commands.Bot(
  command_prefix="!"
)

@client.command()
async def tempmute(ctx, user: diskord.Member, time = None, *, reason: str = None):
    """
    Usage example: !tempmute @SpaceBar#8382 15m Spam his server
    """
    time = humanfriendly.parse_timespan(time)
    now = datetime.datetime.utcnow()
    until = now + datetime.timedelta(seconds=time)

    await user.edit(communication_disabled_until=until, reason=f"{reason}")
    await ctx.send("Member tempmuted!")

client.run("your-token") # <-- replace your-token with your bot's token
