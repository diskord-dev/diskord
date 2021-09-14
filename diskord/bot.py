"""
The MIT License (MIT)

Copyright (c) 2015-present NerdGuyAhmad

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Dict,
    Callable,
    Any,
)
import inspect

from . import utils
from .app_commands import (
    ApplicationCommand,
    SlashCommand,
    UserCommand,
    MessageCommand,
)
from .client import Client
from .enums import ApplicationCommandType
from .interactions import InteractionContext

if TYPE_CHECKING:
    from .interactions import Interaction

class Bot(Client):
    """Represents a bot that interacts with Discord API. 
    
    This inherits from :class:`Client` so anything that is valid there is also valid
    there.

    The purpose of this class is to aid in creation of application commands and other
    features that are not compatible in :class:`Client`. It is highly recommended
    to use this class instead of :class:`Client` if you aim to use application commands
    like slash commands, user & message commands etc. 
    """
    def __init__(self, **options) -> None:
        super().__init__(**options)
        self.__to_register: List[ApplicationCommand] = []
        self._application_commands: Dict[int, ApplicationCommand] = {}
    
    # Commands management
    
    def add_application_command(self, type: ApplicationCommandType, callback: Callable, **attrs) -> ApplicationCommand:
        """Adds an application command to internal list of commands that will be registered on bot connect.
        
        This is generally not called. Instead, :func:`application_command` decorator is used.

        Parameters
        ----------

        cls: Union[:class:`SlashCommand`, :class:`MessageCommand`, :class:`UserCommand`]
            The object type to use.
        callback: Callable
            The callback function for the command.
        
        Returns
        -------

        :class:`ApplicationCommand`
            The registered command.
        """
        types = {
            1: SlashCommand,
            2: UserCommand,
            3: MessageCommand,
        }
        if not type in types:
            raise TypeError('The provided type is not valid.')

        command = types[type](callback, **attrs)
        self.__to_register.append(command)
        
        return command
    
    def remove_application_command(self, command: ApplicationCommand):
        """Removes an application command from internal list of commands that will be registered on bot connect.

        This has no affect when the bot has connected. Use :func:`delete_application_command` instead.

        Parameters
        ----------

        command: :class:`ApplicationCommand`
            The command to delete.
        """
        for cmd in self.__to_register:
            if cmd.id == command.id:
                return self.__to_register.pop(cmd) 

        
    async def register_application_commands(self):
        """|coro|
        
        Register all the application commands that were added using :func:`Bot.add_application_command`
        or decorators.

        This method cleans up previously registered commands and registers all the commands
        that were added using :func:`Bot.add_application_command`.
        
        This function is called under-the-hood inside the :func:`on_connect` event. 

        .. warning::
            If you decided to override the :func:`on_connect` event, You MUST call this manually
            or the commands will not be registered.
        """
        commands = []

        # Firstly, We will register the global commands
        for command in (cmd for cmd in self.__to_register if not cmd.guild_ids):
            data = command.to_dict()
            commands.append(data)
        
        cmds = await self.http.bulk_upsert_global_commands(self.user.id, commands)
        
        for cmd in cmds:
            self._application_commands[int(cmd['id'])] = utils.get(self.__to_register, name=cmd['name'])._from_data(cmd)

        
        # Registering the guild commands now
        
        guilds = {}

        for cmd in (command for command in self.__to_register if command.guild_ids):
            data = cmd.to_dict()
            for guild in cmd.guild_ids:
                guilds[guild] = []
                guilds[guild].append(data)
        
        for guild in guilds:
            cmds = await self.http.bulk_upsert_guild_commands(self.user.id, guild, guilds[guild])
            for cmd in cmds:
                self._application_commands[int(cmd['id'])] = utils.get(self.__to_register, name=cmd['name'])._from_data(cmd)
        
    
    # Decorators

    def slash_command(self, **options) -> SlashCommand:
        """A decorator-based interface to add slash commands to the bot.
        
        This is equivalent of using ``Bot.add_application_command(1, function, **options)``

        Parameters
        ----------

        """
        def inner(func: Callable):
            if not inspect.iscoroutinefunction(func):
                raise TypeError('Callback function must be a coroutine.')
            
            return self.add_application_command(1, func, **options)
        
        return inner
    
    def user_command(self, **options) -> SlashCommand:
        """A decorator-based interface to add user commands to the bot.
        
        This is equivalent of using ``Bot.add_application_command(2, function, **options)``

        Parameters
        ----------

        """
        def inner(func: Callable):
            if not inspect.iscoroutinefunction(func):
                raise TypeError('Callback function must be a coroutine.')
            
            return self.add_application_command(2, func, **options)
        
        return inner

    def message_command(self, **options) -> SlashCommand:
        """A decorator-based interface to add message commands to the bot.
        
        This is equivalent of using ``Bot.add_application_command(3, function, **options)``

        Parameters
        ----------

        """
        def inner(func: Callable):
            if not inspect.iscoroutinefunction(func):
                raise TypeError('Callback function must be a coroutine.')
            
            return self.add_application_command(2, func, **options)
        
        return inner
    
    # Command handler

    async def handle_command_interaction(self, interaction: Interaction) -> Any:
        if not interaction.is_application_command():
            return
        
        command = self._application_commands.get(int(interaction.data['id']))
        
        if not command:
            return
        
        context = await self.get_application_context(interaction)
        await command.callback(context)

    async def get_application_context(self, interaction: Interaction, *, cls: InteractionContext = None) -> InteractionContext:
        if not cls:
            cls = InteractionContext
        
        return cls(self, interaction)

    # Events

    async def on_connect(self):
        await self.register_application_commands()
    
    async def on_interaction(self, interaction: Interaction):
        await self.handle_command_interaction(interaction)