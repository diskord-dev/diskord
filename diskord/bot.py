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
    List,
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
from .message import Message

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

    Attributes
    ----------

    overwrite_application_commands: :class:`bool`
        Whether to overwrite the previously registered commands with new ones or simply
        synchronise them.

        If this is ``True``, :func:`register_application_commands` will be called in 
        :func:`on_connect`, Otherwise :func:`sync_application_commands` will be called.

        This defaults to ``False`` and is strongly recommended to be ``False``.
    """
    def __init__(self, **options) -> None:
        super().__init__(**options)
        self._pending_commands: List[ApplicationCommand] = []
        self._application_commands: Dict[int, ApplicationCommand] = {}
        self.overwrite_application_commands: bool = options.get('overwrite_application_commands', False)

    # Properties

    @property
    def pending_commands(self):
        """
        Returns a list of application commands that will be registered once the bot connects.

        Note that this is most likely to be empty after the bot has connected to Discord because
        all commands are registered as soon as the connection is made.
        
        Returns
        -------

        List[:class:`ApplicationCommands`]
            List of application commands that will be registered. 
        """
        return self._pending_commands

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
        Instead, When that command is sent :func:`on_unknown_application_command` would
        be called.

        .. note::
            To remove a command from API, Use :func:`delete_application_command`

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
    
    async def delete_application_command(self, *,
        guild_id: int = MISSING,
        guild_ids: List[int] = MISSING,
        command_id: int = MISSING, 
        ):
        """|coro|
        
        Deletes an application command.

        .. note::
            This method is an API call. For removing a command from client internal cache,
            Use :func:`remove_application_command` instead.
        
        Parameters
        ----------

        command_id: :class:`int`
            The command's ID to delete.
        guild_id: :class:`int`
            The guild's ID this command belongs to. If not global.
        guild_ids: List[:class:`int`]
            The list of guilds IDs this command belongs to. If not global.

        """
        if guild_id and guild_ids:
            raise TypeError('guild_id and guild_ids parameters cannot be mixed.')
        
        if guild_id:
            guild_ids = [guild_id]
        
        if guild_ids:
            for guild_id in guild_ids:
                await self.http.delete_guild_command(self.user.id, guild_id, command_id)
            
        else:
            await self.http.delete_global_command(self.user.id, command_id)
    
    # TODO: Add other API methods
    
    async def sync_application_commands(self, delete_unregistered_commands: bool = False):
        """|coro|

        Updates the internal cache of application commands with the ones that are already
        registered on the API.

        Unlike :func:`register_application_commands`, This doesn't bulk overwrite the
        registered commands. Instead, it fetches the registered commands and sync the
        internal cache with the new commands.

        This must be used when you don't intend to overwrite all the previous commands but
        want to add new ones.

        This function is called under-the-hood inside the :func:`on_connect` event. 

        .. warning::
            If you decided to override the :func:`on_connect` event, You MUST call this manually
            or the commands will not be registered.

        Parameters
        ----------

        delete_unregistered_commands: :class:`bool`
            Whether or not to delete the commands that were sent by API but are not
            found in internal cache. Defaults to ``False``
        """
        _log.info('Synchronizing internal cache commands.')
        commands = await self.http.get_global_commands(self.user.id)
        non_registered = []

        # Synchronising the fetched commands with internal cache.
        for command in commands:
            registered = utils.get(
                [c for c in self._pending_commands if not c.guild_ids], 
                name=command['name'], 
                type=command['type']
                )
            if registered is None:
                non_registered.append(command)
                continue
            
            self._app_commands[int(command['id'])] = registered
            self._pending_commands.pop(registered)
        
        
        # Deleting the command that weren't found in internal cache
        if delete_unregistered_commands:
            for command in non_registered:
                if command.get('guild_id'):
                    await self.http.delete_guild_command(self.user.id, command['guild_id'], command['id'])
                else:
                    await self.http.delete_global_command(self.user.id, command['id'])
        
        # Registering the remaining commands
        while len(self._pending_commands):
            index = len(self._pending_commands) - 1
            command = self._pending_commands[index]
            if command.guild_ids:
                for guild_id in command.guild_ids:
                    cmd = await self.http.upsert_guild_command(self.user.id, guild_id, command.to_dict())
            else:
                cmd = await self.http.upsert_global_command(self.user.id, command.to_dict())
            
            self._application_commands[int(cmd['id'])] = command
            self._pending_commands.pop(index)
        

    async def register_application_commands(self):
        """|coro|
        
        Register all the application commands that were added using :func:`Bot.add_application_command`
        or decorators.

        This method cleans up previously registered commands and registers all the commands
        that were added using :func:`Bot.add_application_command`.
        
        .. danger:: 
            This function overwrites all the commands and can lead to unexpected issues,
            Consider using :func:`sync_application_commands`
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
                if guilds.get(guild) is None:
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
        
        Usage: ::

            @bot.slash_command(description='My cool slash command.')
            async def test(ctx):
                await ctx.send('Hello world')
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
        
        Usage: ::

            @bot.user_command()
            async def test(ctx):
                await ctx.send('Hello world')
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
        
        Usage: ::

            @bot.message_command()
            async def test(ctx):
                await ctx.send('Hello world')
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

    async def process_application_commands(self, interaction: Interaction) -> Any:
        """|coro|

        Handles an application command interaction. 
        
        This function is used under-the-hood to handle all the application commands interactions.

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
                    await bot.process_application_commands(interaction)
        
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
            self.dispatch('unknown_application_command', interaction)
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
                        state=self._connection,
                        data=resolved['users'][interaction.data['target_id']]
                    )

            return await command.callback(context, user)

        if interaction.data['type'] == ApplicationCommandType.message.value:
            if interaction.guild:
                message = Message(
                    state=interaction.guild._state,
                    channel=interaction.channel,
                    data=interaction.data['resolved']['messages'][interaction.data['target_id']]
                )
            else:
                message = Message(
                    state=self._connection,
                    channel=interaction.user,
                    data=interaction.data['resolved']['messages'][interaction.data['target_id']],
                )
            
            return await command.callback(context, message)

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
        if not self.overwrite_application_commands:
            await self.sync_application_commands()
        else:
            await self.register_application_commands()

    async def on_interaction(self, interaction: Interaction):
        await self.process_application_commands(interaction)

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