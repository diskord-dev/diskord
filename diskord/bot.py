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
import logging

from . import utils
from .app_commands import (
    ApplicationCommand,
    SlashCommand,
    UserCommand,
    MessageCommand,
    Option,
    OptionChoice,
)
from .client import Client
from .enums import (
    ApplicationCommandType,
    OptionType,
    )
from .errors import ApplicationCommandError
from .interactions import InteractionContext
from .member import Member
from .user import User

if TYPE_CHECKING:
    from .interactions import Interaction

_log = logging.getLogger(__name__)
MISSING = utils.MISSING


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
        self._pending_commands: List[ApplicationCommand] = []
        self._application_commands: Dict[int, ApplicationCommand] = {}

    # Properties

    @property
    def application_commands(self):
        """Dict[:class:`int`, :class:`ApplicationCommand`]: Returns a mapping with ID of command to the application command."""
        return self._application_commands
    
    # Commands management
    
    def add_application_command(self, cls: ApplicationCommandType, callback: Callable, **attrs) -> ApplicationCommand:
        """Adds an application command to internal list of commands that will be registered on bot connect.
        
        This is generally not called. Instead, one of the following decorators is used:
        
        * :func:`slash_command`
        * :func:`user_command`
        * :func:`message_command`

        Parameters
        ----------

        cls: :class:`ApplicationCommand`
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
        if not cls in types:
            raise TypeError('The provided type is not valid.')

        command = types[cls](callback, **attrs)
        self._pending_commands.append(command)
        
        if command.type == ApplicationCommandType.slash.value:
            for opt in callback.__annotations__:
                command.add_option(callback.__annotations__[opt])
                
        return command
    
    def remove_application_command(self, id: int, /) -> Optional[ApplicationCommand]:
        """Removes an application command from registered application commands.

        Once an application command is removed using this method, It will not be invoked.

        Parameters
        ----------

        id: :class:`int`
            The ID of command to delete.
        """
        try:
            return self._application_commands.pop(id)
        except KeyError:
            return
    
    def get_application_command(self, id: int, /) -> Optional[ApplicationCommand]:
        """Returns a bot's application command by it's ID.
        
        This function returns ``None`` if the application command is not found.

        Parameters
        ----------
        id: :class:`int`
            The ID of the application command.
        
        Returns
        -------
        Optional[:class:`ApplicationCommand`]
            The command matching the ID.
        """
        return self._application_commands.get(id)

        
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
        # I'm not satisfied with this code?
        # Yes.
        # Rewrite it?
        # Yes.
        # When?
        # idk
        _log.info('Registering %s application commands.' % str(len(self._pending_commands)))
        
        commands = []

        # Firstly, We will register the global commands
        for command in (cmd for cmd in self._pending_commands if not cmd.guild_ids):
            data = command.to_dict()
            commands.append(data)
        
        cmds = await self.http.bulk_upsert_global_commands(self.user.id, commands)
        
        for cmd in cmds:
            self._application_commands[int(cmd['id'])] = utils.get(self._pending_commands, name=cmd['name'])._from_data(cmd)

        
        # Registering the guild commands now
        
        guilds = {}

        for cmd in (command for command in self._pending_commands if command.guild_ids):
            data = cmd.to_dict()
            for guild in cmd.guild_ids:
                guilds[guild] = []
                guilds[guild].append(data)
        
        for guild in guilds:
            cmds = await self.http.bulk_upsert_guild_commands(self.user.id, guild, guilds[guild])
            for cmd in cmds:
                self._application_commands[int(cmd['id'])] = utils.get(self._pending_commands, name=cmd['name'])._from_data(cmd)
        
        _log.info('Registered %s commands successfully.' % str(len(self._pending_commands)))

    
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
            
            return self.add_application_command(
                ApplicationCommandType.slash.value, 
                func, 
                **options
                )
        
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
            
            return self.add_application_command(
                ApplicationCommandType.user.value, 
                func, 
                **options
                )
        
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
            
            return self.add_application_command(
                ApplicationCommandType.message.value, 
                func, 
                **options
                )
        
        return inner
    
    # Command handler

    async def handle_command_interaction(self, interaction: Interaction) -> Any:
        """|coro|

        Handles a command interaction. This function is used under-the-hood to handle all the
        application commands interactions.

        This is internally called in :func:`on_interaction` event.

        .. warning::
            If you decide to override the :func:`on_interaction` event, You must call this at the
            end of your event callback or the commands wouldn't work.

            Usage: ::

                @bot.event
                async def on_interaction(interaction):
                    # do something here
                    ...

                    # at the end of event
                    await bot.handle_command_interaction(interaction)
        
        Parameters
        ----------

        interaction: :class:`Interaction`
            The interaction to handle. If the interaction is not a application command interaction,
            then this will silently ignore the interaction.
        """
        if not interaction.is_application_command():
            return
        
        command = self.get_application_command(int(interaction.data['id']))
                
        if not command:
            _log.info(f'Application command of type {interaction.data["type"]} referencing an unknown command {interaction.data["id"]}, Discarding.')
            return

        self.dispatch('application_command_run', command)

        options = interaction.data.get('options', [])
        kwargs = {}
        context = await self.get_application_context(interaction)

        if interaction.data['type'] == ApplicationCommandType.user.value:
            if interaction.guild:
                user = interaction.guild.get_member(interaction.data['target_id'])
            else:
                user = self.get_user(interaction.data['target_id'])
            
            if user is None:
                resolved = interaction.data['resolved']
                if interaction.guild:
                    member_with_user = resolved['members'][interaction.data['target_id']]
                    member_with_user['user'] = resolved['users'][interaction.data['target_id']]
                    
                    user = Member(
                        data=member_with_user,
                        guild=interaction.guild,
                        state=interaction.guild._state,
                    )
                else:
                    user = User(
                        state=self._state,
                        data=resolved['users'][interaction.data['target_id']]
                    )

            
            return await command.callback(context, user)


        for option in options:
            if option['type'] in (
                OptionType.string.value,
                OptionType.integer.value,
                OptionType.boolean.value,
                OptionType.number.value,
            ):
                value = option['value']

            elif option['type'] == OptionType.user.value:
                if interaction.guild:
                    value = interaction.guild.get_member(int(option['value']))
                else:
                    value = self.get_user(int(option['value']))
            
            elif option['type'] == OptionType.channel.value:
                value = interaction.guild.get_channel(int(option['value']))
                
            elif option['type'] == OptionType.role.value:
                value = interaction.guild.get_role(int(option['value']))
                
            elif option['type'] == OptionType.mentionable.value:
                value = (
                    interaction.guild.get_member(int(option['value'])) or
                    interaction.guild.get_role(int(option['value']))
                    )
                
            kwargs[option['name']] = value

        try:
            await command.callback(context, **kwargs)
        except ApplicationCommandError as error:
            self.dispatch('application_command_error', context, error)
        else:
            self.dispatch('application_command_completion', command)

    async def get_application_context(self, interaction: Interaction, *, cls: InteractionContext = None) -> InteractionContext:
        """|coro|
        
        Gets the :class:`InteractionContext` for an application command interaction.
        
        This function is really useful to add custom contexts. You can override this and
        implement your own context that inherits :class:`InteractionContext` and pass it in ``cls``
        parameter.

        Parameters
        ----------

        interaction: :class:`Interaction`
            The interaction of which context would be returned.
        cls: :class:`InteractionContext`
            The subclass of :class:`InteractionContext` which would be returned. Defaults to :class:`InteractionContext`
        
        Returns
        -------

        :class:`InteractionContext`
            The context of interaction.
        
        Raises
        ------

        TypeError:
            The ``cls`` parameter is not of proper type.
        """
        
        if not cls:
            cls = InteractionContext
        else:
            if not issubclass(cls, InteractionContext):
                raise TypeError('cls parameter must be a subclass of InteractionContext.')

        return cls(self, interaction)

    # Events

    async def on_connect(self):
        await self.register_application_commands()
    
    async def on_interaction(self, interaction: Interaction):
        await self.handle_command_interaction(interaction)

def slash_option(name: str, type_: Any = None,  **attrs) -> Option:
    """A decorator-based interface to add options to a slash command.

    Usage: ::
        
        @bot.slash_command(description="Highfive a member!")
        @diskord.slash_option('member', description='The member to high-five.')
        async def highfive(ctx, member: diskord.Member):
            await ctx.send(f'{ctx.author.name} high-fived {member.name}')
    
    .. warning::
        The callback function must contain the argument and properly annotated or TypeError
        will be raised.
    """
    def inner(func):
        nonlocal type_
        type_ = type_ or func.__annotations__.get(name, MISSING)
        if type_ is MISSING:
            raise TypeError(f'Type for option {name} is not provided.')

        sign = inspect.signature(func).parameters.get(name)
        if sign is None:
            raise TypeError(f'Parameter for option {name} is missing.')

        required = attrs.get('required')
        if required is None:
            required = sign.default is inspect._empty

        func.__annotations__[name] = Option(
            name=name, 
            type=type_, 
            required=required, 
            **attrs
            )
        return func
    
    return inner