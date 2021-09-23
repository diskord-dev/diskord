# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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
    Any,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Tuple,
    Union,
    Callable,
    overload,
)

from . import utils
from .enums import (
    try_enum,
    ApplicationCommandType,
    OptionType,
    ApplicationCommandPermissionType,
)
from .errors import ApplicationCommandError
from .user import User
from .member import Member

if TYPE_CHECKING:
    from .types.interactions import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
        ApplicationCommandPermissions as ApplicationCommandPermissionsPayload,
    )

__all__ = (
    'ApplicationCommand',
    'SlashCommand',
    'SlashSubCommand',
    'SlashSubCommandGroup',
    'UserCommand',
    'MessageCommand',
    'Option',
    'OptionChoice',
)

class OptionChoice:
    """Represents an option choice for an application command's option.


    Attributes
    ----------

    name: :class:`str`
        The name of choice.
    value: :class:`str`
        The value of the choice.
    """
    @overload
    def __init__(self, *,
        name: str = ...,
        value: str = ...,
    ):
        ...

    def __init__(self, *, name: str, value: str):
        self.name  = name
        self.value = value

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
        }

    @classmethod
    def from_dict(cls, dict_: ApplicationCommandOptionChoicePayload):
        return cls(
            name=dict_['name'],
            value=dict_['value']
        )

    def __repr__(self):
        return f'<OptionChoice name={self.name!r} value={self.value!r}'

    def __str__(self):
        return self.name


class Option:
    """Represents an option for an application slash command.

    Attributes
    ----------

    type: :class:`OptionType`
        The type of the option.
    name: :class:`str`
        The name of option.
    description: :class:`str`
        The description of option.
    required: :class:`bool`
        Whether this option is required or not.
    choices: List[:class:`OptionChoice`]
        The list of choices this option has.
    options: List[:class:`Option`]
        The options if the type is a subcommand or subcommand group.
    """
    def __init__(self, **data):
        try:
            self._type: OptionType = OptionType.from_datatype(data.get('type'))
        except TypeError:
            self._type: OptionType = data.get('type')

        self.name: str = data.get('name')
        self.description: str = data.get('description')
        self.required: bool = data.get('required', False)
        self.choices: List[OptionType] = data.get('choices', [])
        self.options: List[Option] = data.get('options', [])
        self.arg: str = data.get('arg', self.name)

    def __repr__(self):
        return f'<Option name={self.name!r} description={self.description!r}>'

    def __str__(self):
        return self.name

    def is_command_or_group(self):
        """:class:`bool`: Indicates whether this option is a subcommand or subgroup."""
        return self.type in (
            OptionType.sub_command.value,
            OptionType.sub_command_group.value,
        )

    def to_dict(self) -> dict:
        dict_ = {
            'type': self.type.value,
            'name': self.name,
            'description': self.description,
            'choices': [],
            'options': [],
        }
        if self.choices:
            dict_['choices'] = [choice.to_dict() for choice in self.choices]

        if self.options:
            dict_['options'] = [option.to_dict() for option in self.options]

        if not self.is_command_or_group():
            dict_['required'] = self.required

        return dict_


# TODO: Work on Application command permissions.


class ApplicationCommandPermissions:
    """Represents the permissions for an application command in a :class:`Guild`.

    Application commands permissions allow you to restrict a guild application command
    to a certain roles or users.

    Attributes
    ----------

    command_id: :class:`int`
        The ID of the command these permissions belong to.
    application_id: :class:`int`
        The ID of application this command belongs to.
    guild_id: :class:`int`
        The ID of the guild this command belongs to.
    permissions: List[:class:`ApplicationCommandPermissions`]
        The list that the commands hold in the guild.
    """
    __slots__ = (
        'command_id',
        'application_id',
        'guild_id',
        'permissions',
    )
    def __init__(self, data: ApplicationCommandPermissionsPayload):
        self.command_id: int = int(data['command_id'])
        self.application_id: int = int(data['application_id'])
        self.guild_id: int = int(data['guild_id'])
        self.permissions: ApplicationCommandPermission = (
            [ApplicationCommandPermission._from_data(perm)
            for perm in data.get('permissions', [])]
        )

class ApplicationCommandPermission:
    """A class representing a specific permission for an application command.

    The purpose of this class is to edit the commands permissions of a command in a guild.
    A number of parameters can be passed in this class initialization to customise
    the permissions.

    Parameters
    ----------

    role: :class:`~abc.Snowflake`
        The ID of role whose permission is defined. This cannot be mixed with ``user``
        parameter.
    user: :class:`~abc.Snowflake`
        The ID of role whose permission is defined. This cannot be mixed with ``role``
        parameter.
    permission: :class:`bool`
        The permission for the command. If this is set to ``False`` the provided
        user or role will not be able to use the command. Defaults to ``False``
    """
    def __init__(self, **options):
        self.user: abc.Snowflake = options.get('user')
        self.role: abc.Snowflake = options.get('role')

        if self.user is None and self.role is None:
            raise TypeError('at least one of role or user keyword parameter must be passed.')

        self.permission: abc.Snowflake = options.get('permission', False)

        if self.user:
            self._id = self.user.id
        elif self.role:
            self._id = self.role.id

    def to_dict(self):
        ret = {
            'id': self._id,
            'permission': self.permission
        }
        if self.user:
            ret['type'] = ApplicationCommandPermissionType.user.value
        elif self.role:
            ret['type'] = ApplicationCommandPermissionType.role.value

        return ret

class ApplicationCommand:
    """Represents an application command. This is base class for all application commands like
    slash commands, user commands etc.

    Attributes
    ----------
    callback: Callable
        The callback function for this command.
    name: :class:`str`
        The name of the command. Defaults to callback's name.
    description: :class:`str`
        The description of this command. Defaults to the docstring of the callback.
    guild_ids: Union[:class:`tuple`, :class:`list`]
        The guild this command will be registered in. Defaults to an empty list for global commands.
    type: :class:`ApplicationCommandType`
        The type of application command.
    id: :class:`int`
        The ID of the command. This can be ``None``.
    application_id: :class:`int`
        The ID of the application command belongs to. This can be ``None``.
    default_permission: :class:`bool`
        Whether the command will be enabled by default or not when added to a guild.
    version: :class:`int`
        The version of command. Can be ``None``
    cog: :class:`diskord.ext.commands.Cog`
        The cog this command is defined in, This will be ``None`` if the command isn't
        defined in any cog.
    """
    def __init__(self, callback: Callable, **attrs):
        self.bot = attrs.get('bot')
        self.callback = callback
        self.name = attrs.get('name') or callback.__name__
        self.description = attrs.get('description') or self.callback.__doc__
        self.guild_ids = attrs.get('guild_ids', [])
        self.cog = None

        if self.type in (
            ApplicationCommandType.user.value,
            ApplicationCommandType.message.value,
        ):
            # Message and User Commands do not have any description.
            # Ref: https://discord.com/developers/docs/interactions/application-commands#user-commands
            # Ref: https://discord.com/developers/docs/interactions/application-commands#message-commands

            self.description = ''

        self._from_data(attrs)

    def _from_data(self, data: ApplicationCommandPayload) -> ApplicationCommand:
        self.id: int = utils._get_as_snowflake(data, 'id')
        self.application_id: int = utils._get_as_snowflake(data, 'application_id')
        self.guild_id: int = utils._get_as_snowflake(data, 'guild_id')
        self.default_permission: bool = data.get('default_permission')
        self.version: int = utils._get_as_snowflake(data, 'version')

        if 'name' in data:
            self.name = data.get('name')
        if 'description' in data:
            self.description = data.get('description')

        return self

    async def _parse_option(self, interaction: Interaction, option: ApplicationCommandOptionPayload) -> Any:
        # This function isn't needed to be a coroutine function but it can be helpful in
        # future so, yes that's the reason it's an async function.

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
                value = context.bot.get_user(int(option['value']))

        elif option['type'] == OptionType.channel.value:
            value = interaction.guild.get_channel(int(option['value']))

        elif option['type'] == OptionType.role.value:
            value = interaction.guild.get_role(int(option['value']))

        elif option['type'] == OptionType.mentionable.value:
            value = (
                interaction.guild.get_member(int(option['value'])) or
                interaction.guild.get_role(int(option['value']))
                )

        return value


    async def invoke(self, context: InteractionContext):
        """|coro|

        Invokes the application command from provided interaction invocation context.

        Parameters
        ----------

        context: :class:`InteractionContext`
            The interaction invocation context.
        """
        interaction: Interaction = context.interaction

        if not interaction.data['type'] == self.type:
            raise TypeError(f'interaction type does not matches the command type. Interaction type is {interaction.data["type"]} and command type is {self.type}')

        if self.type == ApplicationCommandType.user.value:
            if interaction.guild:
                user = interaction.guild.get_member(int(interaction.data['target_id']))
            else:
                user = context.bot.get_user(int(interaction.data['target_id']))

            # below code exists for "just in case" purpose
            if user is None:
                resolved = interaction.data['resolved']
                if interaction.guild:
                    member_with_user = resolved['members'][interaction.data['target_id']]
                    member_with_user['user'] = resolved['users'][interaction.data['target_id']]
                    user = Member(
                        data=member_with_user,
                        guild=interaction.guild,
                        state=interaction.guild._state
                        )
                else:
                    user = User(
                        state=context.bot._connection,
                        data=resolved['users'][interaction.data['target_id']]
                        )

            if self.cog is not None:
                await self.callback(self.cog, context, user)
            else:
                await self.callback(context, user)

            return

        elif self.type == ApplicationCommandType.message.value:
            data = interaction.data['resolved']['messages'][interaction.data['target_id']]
            if interaction.guild:
                message = Message(
                    state=interaction.guild._state,
                    channel=interaction.channel,
                    data=data,
                )
            else:
                message = Message(
                    state=context.bot._connection,
                    channel=interaction.user,
                    data=data,
                )

            if self.cog is not None:
                await self.callback(self.cog, context, message)
            else:
                await self.callback(context, message)

            return



        options = interaction.data.get('options', [])
        kwargs = {}

        for option in options:
            if option['type'] == OptionType.sub_command.value:
                # We will use the name to get the child because
                # subcommands do not have any ID. They are essentially
                # just options of a command. And option names are unique

                sub_options = option.get('options', [])
                for sub_option in sub_options:
                    value = await self._parse_option(interaction, sub_option)
                    kwargs[sub_option['name']] = value

                subcommand = self.get_child(option['name'])

                if subcommand.cog is not None:
                    await subcommand.callback(subcommand.cog, context, **kwargs)
                else:
                    await subcommand.callback(context, **kwargs)

                return

            elif option['type'] == OptionType.sub_command_group.value:
                # In case of sub-command groups interactions, The options array
                # only has one element which is the subcommand that is being used
                # so we essentially just have to get the first element of the options
                # list and lookup the callback function for name of that element to
                # get the subcommand object.

                subcommand_raw = option['options'][0]
                group = self.get_child(option['name'])
                sub_options = subcommand_raw.get('options', [])

                for sub_option in sub_options:
                    value = await self._parse_option(interaction, sub_option)
                    kwargs[sub_option['name']] = value

                subcommand = group.get_child(subcommand_raw['name'])

                if subcommand.cog is not None:
                    await subcommand.callback(subcommand.cog, context, **kwargs)
                else:
                    await subcommand.callback(context, **kwargs)

                return

            else:
                value = await self._parse_option(interaction, option)
                option = self.get_option(option['name'])
                kwargs[option.arg] = value

        if self.cog is not None:
            await self.callback(self.cog, context, **kwargs)
        else:
            await self.callback(context, **kwargs)



    def __repr__(self):
        # More attributes here?
        return f'<ApplicationCommand name={self.name!r} description={self.description!r} guild_ids={self.guild_ids!r}'

    def __str__(self):
        return self.name

class SlashSubCommandGroup(Option):
    """Represents a subcommand group of a slash command.

    A slash subcommand group holds subcommands of that group.

    Example: ::

        @bot.slash_command(description="Edits permission of a role or user.")
        async def permissions(ctx):
            pass

        @permission.sub_command_group(description="Edits permission of a role.")
        async def role(ctx):
            pass

        @role.sub_command(description="Clears the permissions of the role.")
        @diskord.slash_option('role', description='The role to clear permissions of.')
        async def clear(ctx, role: discord.Role):
            await ctx.send('Permissions cleared!')


    In above example, ``/permissions`` is a slash command and ``role`` is a subcommand group
    in that slash command that holds command ``clear`` to use the ``clear`` command, The
    command will be ``/permissions role clear``.

    More command groups can be added in a slash command and similarly, more commands
    can be added into a group.

    Attributes
    ----------

    name: :class:`str`
        The name of command group.
    description: :class:`str`
        The description of command group.
    callback: Callable
        The callback for this command group.
    parent: :class:`SlashCommand`
        The parent command for this group.
    children: List[:class:`SlashSubCommand`]
        The list of commands this subcommand group holds.
    guild_ids: List[:class:`int`]
        A short-hand for :attr:`parent.guild_ids`

        Changing this will have no affect as the guild for a sub-command
        depend upon the guilds of parent command.
    """
    def __init__(self, callback: Callable, parent: SlashCommand, **attrs):
        self.callback = callback
        self.parent = parent
        self.children = []
        super().__init__(
            name=callback.__name__ or attrs.get('name'),
            description=callback.__doc__ or attrs.get('description'),
            type=OptionType.sub_command_group.value,
        )
        self._from_data = parent._from_data

    # parent attributes

    @property
    def guild_ids(self) -> List[int]:
        """List[:class:`int`]: Returns the list of guild IDs in which the parent command is registered."""
        return self.parent.guild_ids

    @property
    def cog(self):
        """Optional[:class:`diskord.ext.commands.Cog`]: Returns the cog of the parent. If parent has no cog, Then None is returned."""
        return self.parent.cog

    # children management

    def get_child(self, name: str, /):
        """
        Gets a child of this command i.e a subcommand or subcommand group of this command
        by the child's name.

        Returns ``None`` if the child is not found.

        Parameters
        ----------
        name: :class:`str`
            The name of the child.

        Returns
        -------
        Union[:class:`SlashSubCommand`, :class:`SlashSubGroup`]
            The required slash subcommand or subcommand group.
        """
        return (utils.get(self.children, name=name))

    def add_child(self, child: SlashSubCommand, /):
        """
        Adds a child i.e subcommand to the command group.

        This shouldn't generally be used. Instead, :func:`sub_command` decorator
        should be used.

        Parameters
        ----------

        child: :class:`SlashSubCommand`
            The child to add.
        """
        self.options.append(child)
        self.children.append(child)

        for opt in child.callback.__annotations__:
            child.add_option(child.callback.__annotations__[opt])

        return child

    def remove_child(self, child: Union[str, SlashSubCommand], /):
        """Removes a child like sub-command or sub-command group from the command.

        Parameters
        ----------

        child: Union[:class:`str`, :class:`SlashSubCommand`]
            The child to remove.
        """
        if isinstance(child, str):
            child = utils.get(self.children, name=child)

        try:
            self.children.remove(child)
        except ValueError:
            return


    # decorators

    def sub_command(self, **attrs):
        """A decorator to register a subcommand in the command group.


        Usage: ::

            @bot.slash_command(description='A cool command that has subcommand groups.')
            async def command(ctx):
                pass

            @command.sub_command_group(description='This is a cool group.')
            async def group(ctx):
                pass

            @group.sub_command(description='This is a cool command inside a command group.')
            async def subcommand(ctx):
                await ctx.send('Hello world!')
        """
        def inner(func: Callable):
            return self.add_child(SlashSubCommand(func, self, **attrs))

        return inner

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'type': OptionType.sub_command_group.value,
            'options': [option.to_dict() for option in self.options],
        }



class SlashSubCommand(Option):
    """Represents a subcommand of a slash command.

    This can be registered using :func:`SlashCommand.sub_command` decorator.

    Example: ::

        @bot.slash_command(description='A cool command that has subcommands.')
        async def git(ctx):
            pass

        @git.sub_command(description='This is git push!')
        async def push(ctx):
            await ctx.send('Pushed!')

    The usage of above command would be like ``/git push``.

    Attributes
    ----------

    name: :class:`str`
        The name of sub-command.
    description: :class:`str`
        The description of sub-command.
    options: List[:class:`Option`]
        The options of sub-command.
    callback: Callable
        The callback for this sub-command.
    parent: :class:`SlashCommand`
        The parent command for this sub-command.
    guild_ids: List[:class:`int`]
        A short-hand for :attr:`parent.guild_ids`

        Changing this will have no affect as the guild for a sub-command
        depend upon the guilds of parent command.
    """
    def __init__(self, callback: Callable, parent: SlashCommand, **attrs):
        self.callback = callback
        self.parent = parent
        super().__init__(
            name=callback.__name__ or attrs.get('name'),
            description=callback.__doc__ or attrs.get('description'),
            type=OptionType.sub_command.value,
        )

        self._from_data = parent._from_data

    # parent attributes

    @property
    def guild_ids(self) -> List[int]:
        """List[:class:`int`]: Returns the list of guild IDs in which the parent command is registered."""
        return self.parent.guild_ids

    @property
    def cog(self):
        """Optional[:class:`diskord.ext.commands.Cog`]: Returns the cog of the parent. If parent has no cog, Then None is returned."""
        return self.parent.cog

    def to_dict(self) -> dict:
        options = self.options
        options.reverse()

        dict_ = {
            'name': self.name,
            'description': self.description,
            'type': OptionType.sub_command.value,
            'options': [option.to_dict() for option in options],
        }
        return dict_

    def add_option(self, option: Option) -> Option:
        """Adds an option to this slash command.

        Parameters
        ----------
        option: :class:`Option`
            The option to add.

        Returns
        -------
        :class:`Option`
            The added option.

        """
        if not isinstance(option, Option):
            raise TypeError('option must be an instance of Option class.')

        self.options.append(option)
        return option



class SlashCommand(ApplicationCommand):
    """Represents a slash command.

    A slash command is a user input command that a user can use by typing ``/`` in
    the chat.

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.slash`

    Attributes
    ----------

    type: :class:`ApplicationCommandType`
        The type of command, Always :attr:`ApplicationCommandType.slash`
    options: List[:class:`Option`]
        The list of options this command has.

        .. tip::
            To get only the children i.e sub-commands and sub-command groups,
            Consider using :attr:`children`

    children: List[:class:`SlashSubCommand`, `SlashSubCommandGroup`]
        The children of this commands i.e sub-commands and sub-command groups.
    """
    def __init__(self, callback, **attrs):
        self.type = ApplicationCommandType.slash.value
        self.options: List[Option] = []
        self.children: List[SlashSubCommand, SlashSubCommandGroup] = []

        # To stay consistent with the discord.ext.commands models, I added this
        # parent attribute here which will always be None in case of this.
        # this is not documented for obvious reason.
        self.parent = None

        super().__init__(callback, **attrs)

    def get_option(self, name: str) -> Optional[Option]:
        """Gets an option by it's name.

        This function returns None if the option is not found.

        Parameters
        ----------
        name: :class:`str`
            The name of option

        Returns
        -------
        Optional[:class:`Option`]:
            The required option.
        """
        return utils.get(self.options, name=name)


    def add_option(self, option: Option) -> Option:
        """Adds an option to this slash command.

        Parameters
        ----------
        option: :class:`Option`
            The option to add.

        Returns
        -------
        :class:`Option`
            The added option.

        """
        if not isinstance(option, Option):
            raise TypeError('option must be an instance of Option class.')

        self.options.append(option)
        return option

    def remove_option(self, name: str, /):
        """Removes an option from the command by it's name.

        If an error is raised, then it is silently swallowed by this function.

        Parameters
        ----------
        name: :class:`str`
            The name of option.
        """
        try:
            self.options.remove(utils.get(self.options), name=name)
        except ValueError:
            return


    # children management

    def get_child(self, name: str, /):
        """
        Gets a child of this command i.e a subcommand or subcommand group of this command
        by the child's name.

        Returns ``None`` if the child is not found.

        Parameters
        ----------
        name: :class:`str`
            The name of the child.

        Returns
        -------
        Union[:class:`SlashSubCommand`, :class:`SlashSubGroup`]
            The required slash subcommand or subcommand group.
        """
        return (utils.get(self.children, name=name))

    def add_child(self, child: SlashSubCommand, /):
        """
        Adds a child i.e subcommand to the command group.

        This shouldn't generally be used. Instead, :func:`sub_command` decorator
        should be used.

        Parameters
        ----------

        child: :class:`SlashSubCommand`
            The child to add.
        """
        self.options.append(child)
        self.children.append(child)

        for opt in child.callback.__annotations__:
            child.add_option(child.callback.__annotations__[opt])

        return child

    def remove_child(self, name: str, /):
        """Removes a child like sub-command or sub-command group from the command.

        Parameters
        ----------

        child: :class:`str`
            The child to remove.
        """
        child = utils.get(self.children, name=name)

        try:
            self.children.remove(child)
        except ValueError:
            return


    # decorators

    def sub_command(self, **attrs):
        """A decorator to register a subcommand within a slash command.

        .. note::
            Once a slash sub-command is registered the callback for parent command
            would not work. For example:

            ``/hello`` is not a valid command because it has two subcommands ``foo`` and ``world``
            so ``/hello foo`` and ``/hello world`` are two valid commands.

        Usage: ::

            @bot.slash_command(description='A cool command that has subcommands.')
            async def git(ctx):
                pass

            @git.sub_command(description='This is git push!')
            async def push(ctx):
                await ctx.send('Pushed!')

        Options and other features can be added to the subcommands.
        """
        def inner(func: Callable):
            return self.add_child(SlashSubCommand(func, self, **attrs))

        return inner

    def sub_command_group(self, **attrs):
        """A decorator to register a subcommand group within a slash command.


        Usage: ::

            @bot.slash_command(description='A cool command that has subcommand groups.')
            async def command(ctx):
                pass

            @command.sub_command_group(description='This is a cool group.')
            async def group(ctx):
                pass

            @group.sub_command(description='This is a cool command inside a command group.')
            async def subcommand(ctx):
                await ctx.send('Hello world!')
        """
        def inner(func: Callable):
            return self.add_child(SlashSubCommandGroup(func, self, **attrs))

        return inner

    def to_dict(self) -> dict:
        # We're reversing the options list here because the order of how options are
        # registered using decorator is below-to-top so we have to reverse it to
        # normalize the list. The core reason is that discord API does not
        # allow to put the non-required options before required ones which makes sense.

        reversed_options = self.options
        reversed_options.reverse()

        dict_ = {
            'name': self.name,
            'type': self.type,
            'options': [option.to_dict() for option in reversed_options],
            'description': self.description,
        }

        return dict_


class UserCommand(ApplicationCommand):
    """Represents a user command.

    A user command can be used by right-clicking a user in discord and choosing the
    command from "Apps" context menu

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.user`
    """
    def __init__(self, callback, **attrs):
        self.type = ApplicationCommandType.user.value
        super().__init__(callback, **attrs)


    def to_dict(self) -> dict:
        dict_ = {
            'name': self.name,
            'description': self.description,
            'type': self.type,
        }
        return dict_

class MessageCommand(ApplicationCommand):
    """Represents a message command.

    A message command can be used by right-clicking a message in discord and choosing
    the command from "Apps" context menu.

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.message`
    """
    def __init__(self, callback, **attrs):
        self.type = ApplicationCommandType.message.value
        super().__init__(callback, **attrs)


    def to_dict(self) -> dict:
        dict_ = {
            'name': self.name,
            'description': self.description,
            'type': self.type,
        }
        return dict_
