# diskord
A modern, easy to use, feature-rich, and async ready API wrapper for Discord written in Python.

This library is a maintained and work-in-progress fork of the popular library, [discord.py](https://github.com/Rapptz/discord.py) which was discontinued on August 28th, 2021. You can see more [here](https://gist.github.com/Rapptz/4a2f62751b9600a31a0d3c78100287f1).

## Key features
* Modern Pythonic API using `async` and `await`.
* Proper rate limit handling.
* Optimised in both speed and memory.
* Actively maintained
* Implements the entire Discord API

## Installation
**Python 3.8 or higher** is required

To install the library **without** full voice support, you can just run the following command:
```sh
# Linux/macOS
python3 -m pip install -U discord.py

# Windows
py -3 -m pip install -U discord.py
```
Otherwise to get voice support you should run the following command:

```sh
# Linux/macOS
python3 -m pip install -U "discord.py[voice]"

# Windows
py -3 -m pip install -U discord.py[voice]
```
To install the development version, do the following:

```sh
$ git clone https://github.com/Rapptz/discord.py
$ cd discord.py
$ python3 -m pip install -U .[voice]
```

### Optional Packages
* PyNaCl (for voice support)
Please note that on Linux installing voice you must install the following packages via your favourite package manager (e.g. `apt`, `dnf`, etc) before running the above commands:

* libffi-dev (or `libffi-devel` on some systems)
* python-dev (e.g. `python3.6-dev` for Python 3.6)

## Quick Example
```py
import discord

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == 'ping':
            await message.channel.send('pong')

client = MyClient()
client.run('token')
```

## Bot Example
```py
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='>')

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

bot.run('token')
```
You can find more examples in the examples directory.

## Links
* [Documentation](https://diskord.readthedocs.io/en/latest/index.html)
* [Official Discord Server](https://dsc.gg/diskord-dev)
* [Discord API](https://discord.gg/discord-api)
