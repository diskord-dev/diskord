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
    Literal,
)
import inspect
import functools

from . import utils
from .enums import (
    try_enum,
    ApplicationCommandType,
    OptionType,
    ApplicationCommandPermissionType,
)
from .errors import ApplicationCommandError, ApplicationCommandCheckFailure
from .user import User
from .member import Member
from .interactions import InteractionContext

if TYPE_CHECKING:
    from .types.interactions import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
        ApplicationCommandPermissions as ApplicationCommandPermissionsPayload,
    )

__all__ = (
    'ApplicationCommand',
    'ApplicationCommandGuildPermissions',
    'ApplicationCommandPermission',
    'SlashCommand',
    'SlashCommandChild',
    'SlashSubCommand',
    'SlashCommandGroup',
    'UserCommand',
    'MessageCommand',
    'Option',
    'OptionChoice',
    'slash_option',
    'slash_command',
    'user_command',
    'message_command',
    'application_command_permission',
)

def unwrap_function(function: Callable[..., Any]) -> Callable[..., Any]:
    partial = functools.partial
    while True:
        if hasattr(function, '__wrapped__'):
            function = function.__wrapped__
        elif isinstance(function, partial):
            function = function.func
        else:
            return function

def get_signature_parameters(function: Callable[..., Any], globalns: Dict[str, Any]) -> Dict[str, inspect.Parameter]:
    signature = inspect.signature(function)
    params = {}
    cache: Dict[str, Any] = {}
    eval_annotation = utils.evaluate_annotation
    for name, parameter in signature.parameters.items():
        annotation = parameter.annotation
        if annotation is parameter.empty:
            params[name] = parameter
            continue
        if annotation is None:
            params[name] = parameter.replace(annotation=type(None))
            continue

        annotation = eval_annotation(annotation, globalns, globalns, cache)
        params[name] = parameter.replace(annotation=annotation)

    return params

Check = Callable[[InteractionContext, 'Context'], bool]

class OptionChoice:
    """Represents an option choice for an application command's option.

    Attributes
    ----------

    name: :class:`str`
        The name of choice. Will be shown on command explorer.
    value: :class:`str`
        A user-set value of the choice. Will be passed in the command's callback.
    """
    def __init__(self, *, name: str, value: str):
        self.name  = name
        self.value = value

        self._option: Option = None # type: ignore

    @property
    def option(self) -> Option:
        """:class:`Option`: The parent option of this choice."""
        return self._option


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

    This class is generally not initialized manually, Instead :func:`.option` decorator
    interface is used.

    .. info::
        All parameters except ``name`` and ``description`` are optional.

    Parameters
    ----------
    name: :class:`str`
        The name of option.
    description: :class:`str`
        The description of option. Defaults to ``No description``
    type: :class:`OptionType`
        The type of the option. Defaults to :attr:`OptionType.string`
        While using :func:`.option` decorator, This is determined by type or annotation
        of relevant argument of parent command callback function.
    required: :class:`bool`
        Whether this option is required or not. Defaults to ``True``
        While using :func:`.option` decorator, This is determined by the argument
        of parent command callback function.
    arg: :class:`str`
        The argument name which represents this option in callback function.
    choices: List[:class:`OptionChoice`]
        The list of choices this option has.
    converter: Optional[:class:`~ext.commands.Converter`]
        The converter of this option. This is derived directly from converters in 
        commands extension. Read about :class:`ext.commands.Converter`
    channel_types: List[:class:`ChannelType`]
        The channel types to show, If :attr:`Option.type` is :attr:`OptionType.channel`.
        This is determined by the annotation of the option in callback function.
    """
    def __init__(self, *,
        name: str,
        description: str = None,
        type: OptionType = str,
        choices: List[OptionChoice] = None,
        required: bool = True,
        arg: str = None,
        converter: 'Converter' = None,
        **attrs,
    ):
        self._callback: Callable[..., Any] = attrs.get('callback')
        self._name = name
        self._description = description or "No description"
        self._required = required
        self._arg = arg or self.name
        self._channel_types: List[ChannelType] = attrs.get('channel_types', []) # type: ignore
        self._choices: List[OptionChoice] = choices
        if self._choices is None:
            self._choices = []

        self._options: List[Option] = []
        self.converter: 'Converter' = converter # type: ignore

        self._parent: Union[ApplicationCommand, Option] = None # type: ignore

        if type in [OptionType.sub_command_group, OptionType.sub_command]:
            self._type = type
        else:
            try:
                self._type: OptionType = OptionType.from_datatype(type, option=self)
            except TypeError:
                self._type: OptionType = type

    def __repr__(self):
        return f'<Option name={self._name!r} description={self._description!r}>'

    def __str__(self):
        return self._name

    # properties
    @property
    def name(self) -> str:
        """:class:`str`: The name of option."""
        return self._name

    @property
    def channel_types(self) -> List[ChannelType]:
        """List[:class:`ChannelType`]: The channel types to show, If :attr:`Option.type` 
        is :attr:`OptionType.channel`.

        .. info::
            Though this is determined by the annotation of parameter that represents
            this option in the callback function, It should be noted that due to how 
            Discord's Enum work, For precise selection of channel types, Pass the list of 
            desired :class:`ChannelType` in ``channel_types`` parameter in :class:`Option`
        """
        return self._channel_types


    @property
    def description(self) -> str:
        """:class:`str`: The description of option."""
        return self._description

    @property
    def type(self) -> OptionType:
        """:class:`OptionType`: The :class:`OptionType` of the option."""
        return self._type

    @property
    def required(self) -> bool:
        """:class:`bool`: Whether the option is required or not."""
        return self._required

    @property
    def parent(self) -> Union[ApplicationCommand, Option]:
        """
        Union[:class:`ApplicationCommand`, :class:`Option`]: The parent of
        this option i.e the command or sub-command.
        """
        return self._parent

    @property
    def choices(self) -> List[OptionChoice]:
        """List[:class:`OptionChoice`]: The list of choices of this option."""
        return self._choices

    @property
    def options(self) -> List[Option]:
        """List[:class:`Option`]: The list of sub-options of this option."""
        return self._options

    @property
    def arg(self) -> str:
        """:class:`str`: Returns the name of argument that represents this option in callback function."""
        return self._arg

    # Choices management

    def get_choice(self, **attrs) -> Optional[OptionChoice]:
        """Gets a choice that matches the provided traits.

        Parameters
        ----------
        name: :class:`str`
            The name of choice.
        value: :class:`str`
            The value of choice.

        Returns
        -------
        Optional[:class:`OptionChoice`]
            The removed choice. ``None`` if not found.
        """
        return utils.get(self._choices, **attrs)

    def add_choice(self, *, index: int = -1, **attrs) -> OptionChoice:
        """Adds a choice to option.

        To append a choice, Use :func:`Option.append_choice`.

        Parameters
        ----------
        name: :class:`str`
            The name of choice. Will be shown on command explorer.
        value: :class:`str`
            A user-set value of the choice. Will be passed in the command's callback.
        index: :class:`int`
            The position to insert the choice at.

        Returns
        -------
        :class:`OptionChoice`
            The added choice.
        """
        choice = OptionChoice(**attrs)
        choice._option = self
        self._choices.insert(index, choice)
        return choice

    def append_choice(self, choice: OptionChoice) -> OptionChoice:
        """Appends a choice to option's choice.

        Parameters
        ----------
        choice: :class:`OptionChoice`
            The choice to append.

        Returns
        -------
        :class:`OptionChoice`
            The appended choice.
        """
        choice._option = self
        self._choices.append(choice)
        return choice

    def remove_choice(self, **attrs) -> Optional[OptionChoice]:
        """Removes the choice that matches the provided traits.

        At least one of ``name`` or ``value`` parameter must be provided.

        If choice is not found, ``None`` would be returned.

        Parameters
        ----------
        name: :class:`str`
            The name of choice.
        value: :class:`str`
            The value of choice.

        Returns
        -------
        Optional[:class:`OptionChoice`]
            The removed choice. ``None`` if not found.
        """
        choice = utils.get(self._choices, **attrs)
        if choice:
            self._choices.remove(choice)

        return choice

    # Options management

    def get_option(self, **attrs) -> Optional[Option]:
        """Gets an option that matches the provided traits.

        Parameters
        ----------
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        Optional[:class:`OptionChoice`]
            The option that matched the traits. ``None`` if not found.
        """
        return utils.get(self._options, **attrs)

    def add_option(self, *, index: int = -1, **attrs) -> Option:
        """Adds a sub-option to option.

        To append an option, Use :func:`Option.append_option`.

        Parameters
        ----------
        index: :class:`int`
            The index to insert at. Defaults to ``-1`` aka end of options list.
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        :class:`Option`
            The added choice.
        """
        option = Option(**attrs)
        option._parent = self
        self._options.insert(index, option)
        return option

    def append_option(self, option: Option) -> Option:
        """Appends a sub-option to end of sub-options list.

        Parameters
        ----------
        option: :class:`Option`
            The option to append.

        Returns
        -------
        :class:`Option`
            The appended option.
        """
        option._parent = self
        self._options.append(option)
        return option

    def remove_option(self, **attrs) -> Optional[Option]:
        """Removes the sub-option that matches the provided traits.

        If option is not found, ``None`` would be returned.

        Parameters
        ----------
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        Optional[:class:`Option`]
            The removed choice. ``None`` if not found.
        """
        option = utils.get(self._options, **attrs)
        if option:
            self._options.remove(option)

        return option

    def is_command_or_group(self):
        """:class:`bool`: Indicates whether this option is a subcommand or subgroup."""
        return self._type.value in (
            OptionType.sub_command.value,
            OptionType.sub_command_group.value,
        )

    def to_dict(self) -> dict:
        dict_ = {
            'type': self._type.value,
            'name': self._name,
            'description': self._description,
            'choices': [choice.to_dict() for choice in self._choices],
            'options': [option.to_dict() for option in self.options],
        }

        if not self.is_command_or_group():
            # Discord API doesn't allow passing required in the payload of
            # options that have type of 1 or 2.
            dict_['required'] = self._required

        if self._channel_types:
            dict_['channel_types'] = []
            for t in self._channel_types:
                if isinstance(t, list):
                    for st in t:
                        dict_['channel_types'].append(st.value)
                else:
                    dict_['channel_types'].append(t.value)

        return dict_



class ApplicationCommandGuildPermissions:
    """Represents the permissions for an application command in a :class:`Guild`.

    Application commands permissions allow you to restrict an application command
    to a certain roles or users.

    Attributes
    ----------
    permissions: List[:class:`ApplicationCommandGuildPermissions`]
        The list that the commands hold in the guild.
    """
    def __init__(self, *,
        command_id: int,
        application_id: int,
        guild_id: int,
        permissions: List[ApplicationCommandPermission]
        ):
        self._command_id = command_id
        self._application_id = application_id
        self._guild_id = guild_id
        self._permissions = permissions

        self._command: ApplicationCommand = None # type: ignore


    @property
    def command(self) -> ApplicationCommand:
        """:class:`ApplicationCommand`: The command these permissions belongs to."""
        return self._command


    @property
    def command_id(self) -> int:
        """:class:`int`: The ID of the command these permissions belong to."""
        return self._command_id

    @property
    def application_id(self) -> int:
        """:class:`int`: The ID of application this command belongs to."""
        return self._application_id

    @property
    def guild_id(self) -> int:
        """:class:`int`: The ID of guild this application command belongs to."""
        return self._guild_id

    def to_dict(self) -> dict:
        return {
            'command_id': self._command_id,
            'application_id': self._application_id,
            'guild_id': self._guild_id,
            'permissions': [perm.to_dict() for perm in self._permissions],
        }

class ApplicationCommandPermission:
    """A class representing a specific permission for an application command.

    The purpose of this class is to edit the commands permissions of a command in a guild.
    A number of parameters can be passed in this class initialization to customise
    the permissions.

    Parameters
    ----------

    id: :class:`int`
        The ID of role or user whose permission is being defined.
    type: :class:`ApplicationCommandPermissionType`
        The type of permission. If a role id was passed in ``id`` parameter
        then this should be :attr:`ApplicationCommandPermissionType.role`
        and if user id was passed then it should  be
        :attr:`ApplicationCommandPermissionType.user`
    permission: :class:`bool`
        The permission for the command. If this is set to ``False`` the provided
        user or role will not be able to use the command. Defaults to ``False``
    """
    def __init__(self, *, id: int, type: ApplicationCommandPermissionType, permission: bool):
        self.id = id
        self.type = type
        self.permission = bool(permission)

    def to_dict(self):
        ret = {
            'id': self.id,
            'permission': self.permission,
            'type': self.type.value,
        }

        return ret

class ApplicationCommand:
    """Represents an application command. This is base class for all application commands like
    slash commands, user commands etc.

    Parameters
    ----------
    checks: List[Callable[:class:`InteractionContext`, bool]]
        The list of checks this commands holds that will be checked before command's
        invocation.

        For more info on checks and how to register them, See :func:`~ext.commands.check` 
        documentation as these checks actually come from there.
    """
    def __init__(self, callback: Callable, **attrs: Any):
        self._callback = callback
        self._name = attrs.get('name') or getattr(callback, '__name__', None)
        self._description = attrs.get('description', callback.__doc__) or 'No description'
        self._guild_ids   = attrs.get('guild_ids', [])
        self._default_permission = attrs.get('default_permission')

        self._cog = None
        self._id  = None
        self._application_id = None
        self._version = None
        self._client = self._bot = None

        if hasattr(callback, '__application_command_permissions__'):
            self._permissions = callback.__application_command_permissions__
        else:
            self._permissions: List[ApplicationCommandGuildPermissions] = [] # type: ignore

        for perm in self._permissions:
            perm._command = self

        if self._type in (
            ApplicationCommandType.user,
            ApplicationCommandType.message,
        ):
            # Message and User Commands do not have any description.
            # Ref:
            # https://discord.com/developers/docs/interactions/application-commands#user-commands
            # https://discord.com/developers/docs/interactions/application-commands#message-commands

            self.description = ''


        try:
            checks = self._callback.__commands_checks__
            checks.reverse()
        except AttributeError:
            checks = attrs.get('checks', [])

        self.checks: List[Check] = checks

    def is_global_command(self) -> bool:
        """:class:`bool`: Whether the command is global command or not."""
        return bool(self._guild_ids)

    def _from_data(self, data: ApplicationCommandPayload) -> ApplicationCommand:
        self._id: int = utils._get_as_snowflake(data, 'id')
        self._application_id: int = utils._get_as_snowflake(data, 'application_id')
        self._guild_id: int = utils._get_as_snowflake(data, 'guild_id')
        self._version: int = utils._get_as_snowflake(data, 'version')

        if 'name' in data:
            self._name = data.get('name')
        if 'description' in data:
            self._description = data.get('description')
        if 'default_permission' in data:
            self._default_permission = data.get('default_permission')

        # permissions don't have all of their attributes set so we have to set them
        # properly

        return self

    def update(self, **attrs) -> ApplicationCommand:
        """Updates the command with new traits provided in ``attrs``

        Parameters
        ----------
        **attrs:
            The new attributes to update command with.

        Returns
        -------
        :class:`ApplicationCommand`
            The new commands.
        """
        forbidden_keys = (
            'id',
            'guild_id',
            'application_id',
            'version',
            'cog'
        )
        for attr in attrs:
            if f'_{attr}' in self.__dict__ and attr in forbidden_keys:
                setattr(self, f'_{attr}', attrs[attr])

    @property
    def permissions(self) -> List[ApplicationCommandGuildPermissions]:
        """List[:class:`ApplicationCommandGuildPermissions`]: List of permissions this command holds."""
        return self._permissions

    @property
    def callback(self) -> Callable:
        """Callable[..., Any]: Returns the command's callback function."""
        return self._callback

    @property
    def name(self) -> str:
        """:class:`str`: The name of application command."""
        return self._name

    @property
    def description(self) -> str:
        """:class:`description`: The description of application command."""
        return self._description

    @property
    def guild_ids(self) -> List[int]:
        """List[:class:`int`]: The list of guild IDs in which this command will/was register.

        Unlike :attr:`ApplicationCommand.guild_id` this is the list of guild IDs in which command
        will register on the bot's connect.
        """
        return self._guild_ids

    @property
    def guild_id(self) -> int:
        """:class:`int`: The ID of the guild this command belongs to.

        Every command is stored per-guild basis and this attribute represents that guild's ID.
        To get the list of guild IDs in which this command was initially registered, use
        :attr:`ApplicationCommand.guild_id`
        """
        return self._guild_id

    @property
    def type(self) -> ApplicationCommandType:
        """:class:`ApplicationCommandType`: Returns the type of application command."""
        return self._type

    @property
    def default_permission(self) -> bool:
        """
        :class:`bool`: Returns the default permission of this command. Default permission
        means whether this command will be enabled by default or not. ``False`` indicates
        that this command is not useable by default.
        """
        return self._default_permission

    @property
    def id(self) -> Optional[int]:
        """
        Optional[:class:`int`]: The unique ID of this command. This is usually ``None`` before command
        registration.
        """
        return self._id

    @property
    def application_id(self) -> Optional[int]:
        """
        Optional[:class:`int`]: The ID of application that owns this command usually :attr:`ClientUser.id`.
        This is usually ``None`` before command registration.
        """
        return self._application_id

    @property
    def version(self) -> Optional[int]:
        """
        Optional[:class:`int`]: The unique version of the application command. Usually
        :attr:`ApplicationCommand.id`
        """
        return self._version

    @property
    def cog(self):
        """
        Optional[:class:`ext.commands.Cog`]: Returns the cog in which this command was
        registered. If command has no cog, then ``None`` is returned.
        """
        return self._cog

    # checks management

    def add_check(self, predicate: Check):
        """
        Adds a check to the command.

        This is the non-decorator interface to :func:`.check`.

        .. versionadded:: 2.0

        Parameters
        -----------
        predicate
            The function that will be used as a check.
        """
        self.checks.append(predicate)
        return predicate

    def remove_check(self, func: Check) -> None:
        """Removes a check from the command.

        This function is idempotent and will not raise an exception
        if the function is not in the command's checks.

        .. versionadded:: 2.0

        Parameters
        -----------
        func
            The function to remove from the checks.
        """

        try:
            self.checks.remove(func)
        except ValueError:
            pass

    async def can_run(self, ctx: InteractionContext) -> bool:
        """|coro|

        Checks if the command can be executed by checking all the predicates
        inside the :attr:`~ApplicationCommand.checks` attribute. This also checks whether the
        command is disabled.

        .. versionchanged:: 2.0
            Checks whether the command is disabled or not

        Parameters
        -----------
        ctx: :class:`InteractionContext`
            The ctx of the command currently being invoked.

        Raises
        -------
        :class:`ApplicationCommandError`
            Any command error that was raised during a check call will be propagated
            by this function.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command can be invoked.
        """
        cog = self.cog
        if cog is not None:
            local_check = type(cog)._get_overridden_method(cog.cog_check)
            if local_check is not None:
                ret = await utils.maybe_coroutine(local_check, ctx)
                if not ret:
                    return False

        predicates = self.checks
        if not predicates:
            # since we have no checks, then we just return True.
            return True

        return await utils.async_all(predicate(ctx) for predicate in predicates)  # type: ignore

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
                value = context.client.get_user(int(option['value']))

            # value can be none in case when member intents are not available

            if value is None:
                resolved = interaction.data['resolved']
                if interaction.guild:
                    member_with_user = resolved['members'][option['value']]
                    member_with_user['user'] = resolved['users'][option['value']]
                    value = Member(
                        data=member_with_user,
                        guild=interaction.guild,
                        state=interaction.guild._state
                        )
                else:
                    value = User(
                        state=context.client._connection,
                        data=resolved['users'][option['value']]
                        )

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
        command = None
        args = [context]

        if not interaction.data['type'] == self.type.value:
            raise TypeError(f'interaction type does not matches the command type. Interaction type is {interaction.data["type"]} and command type is {self.type}')

        if self.type == ApplicationCommandType.user.value:
            if interaction.guild:
                user = interaction.guild.get_member(int(interaction.data['target_id']))
            else:
                user = context.client.get_user(int(interaction.data['target_id']))

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
                        state=context.client._connection,
                        data=resolved['users'][interaction.data['target_id']]
                        )

            args.append(user)
            command = self

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
                    state=context.client._connection,
                    channel=interaction.user,
                    data=data,
                )

            args.append(message)
            command = self

        options = interaction.data.get('options', [])
        kwargs = {}

        for option in options:
            if option['type'] == OptionType.sub_command.value:
                # We will use the name to get the child because
                # subcommands do not have any ID. They are essentially
                # just options of a command. And option names are unique

                subcommand = self.get_child(name=option['name'])
                context.command = subcommand
                sub_options = option.get('options', [])

                for sub_option in sub_options:
                    value = await self._parse_option(interaction, sub_option)
                    resolved = subcommand.get_option(name=sub_option['name'])
                    if resolved.converter is not None:
                        kwargs[resolved.arg] = await resolved.converter().convert(context, value)
                    else:
                        kwargs[resolved.arg] = value

                command = subcommand
                break

            elif option['type'] == OptionType.sub_command_group.value:
                # In case of sub-command groups interactions, The options array
                # only has one element which is the subcommand that is being used
                # so we essentially just have to get the first element of the options
                # list and lookup the callback function for name of that element to
                # get the subcommand object.

                subcommand_raw = option['options'][0]
                group = self.get_child(name=option['name'])
                sub_options = subcommand_raw.get('options', [])
                subcommand = group.get_child(name=subcommand_raw['name'])
                context.command = subcommand

                for sub_option in sub_options:
                    value = await self._parse_option(interaction, sub_option)
                    resolved = subcommand.get_option(name=sub_option['name'])

                    if resolved.converter is not None:
                        kwargs[resolved.arg] = await resolved.converter().convert(context, value)
                    else:
                        kwargs[resolved.arg] = value

                command = subcommand
                break

            else:
                if command is None:
                    command = self
                    context.command = command

                value = await self._parse_option(interaction, option)
                option = self.get_option(name=option['name'])

                if option.converter is not None:
                    kwargs[option.arg] = await option.converter().convert(context, value)
                else:
                    kwargs[option.arg] = value

        if not (await command.can_run(context)):
            # todo: do this before options parsing.
            raise ApplicationCommandCheckFailure(f'checks functions for application command {command._name} failed.')

        if command.cog is not None:
            await command.callback(command.cog, *args, **kwargs)
        else:
            await command.callback(*args, **kwargs)

    def __repr__(self):
        # More attributes here?
        return f'<ApplicationCommand name={self.name!r} description={self.description!r} guild_ids={self.guild_ids!r}'

    def __str__(self):
        return self.name

class SlashCommandChild(Option):
    """
    Base class for slash commands children like :class:`SlashCommandGroup` and
    :class:`SlashSubCommand`.

    This class subclasses :class:`Option` so all attributes of option class are valid here.

    This class is not meant to be used in general and is here for documentation-purposes only.
    For general use, Use the subclasses of this class like  :class:`SlashCommandGroup` and
    :class:`SlashSubCommand`.
    """
    def __init__(self, callback: Callable,
        type: SlashChildType, *,
        name: str = None,
        description: str = None,
        **kwargs
    ):
        super().__init__(
            name=name or callback.__name__,
            description=description or callback.__doc__ or 'No description.',
            type=type,
        )
        self._callback = callback
        self._parent = None


        try:
            checks = self._callback.__commands_checks__
            checks.reverse()
        except AttributeError:
            checks = kwargs.get('checks', [])

        self.checks: List[Check] = checks

    @property
    def guild_ids(self) -> List[int]:
        """List[:class:`int`]: Returns the list of guild IDs in which the parent command is registered."""
        return self.parent.guild_ids

    @property
    def cog(self):
        """Optional[:class:`diskord.ext.commands.Cog`]: Returns the cog of the parent. If parent has no cog, Then None is returned."""
        return self.parent.cog

    @property
    def parent(self) -> SlashCommand:
        """:class:`SlashCommand`: The parent command of this child command."""
        return self._parent

    @property
    def callback(self) -> SlashCommand:
        """Callable: The callback function for this child."""
        return self._callback

    # checks management

    def add_check(self, predicate: Check):
        """
        Adds a check to the command.

        This is the non-decorator interface to :func:`.check`.

        .. versionadded:: 2.0

        Parameters
        -----------
        predicate
            The function that will be used as a check.
        """
        self.checks.append(predicate)
        return predicate

    def remove_check(self, func: Check) -> None:
        """Removes a check from the command.

        This function is idempotent and will not raise an exception
        if the function is not in the command's checks.

        .. versionadded:: 2.0

        Parameters
        -----------
        func
            The function to remove from the checks.
        """

        try:
            self.checks.remove(func)
        except ValueError:
            pass

    async def can_run(self, ctx: InteractionContext) -> bool:
        """|coro|

        Checks if the command can be executed by checking all the predicates
        inside the :attr:`~ApplicationCommand.checks` attribute. This also checks whether the
        command is disabled.

        .. versionchanged:: 2.0
            Checks whether the command is disabled or not

        Parameters
        -----------
        ctx: :class:`InteractionContext`
            The ctx of the command currently being invoked.

        Raises
        -------
        :class:`ApplicationCommandError`
            Any command error that was raised during a check call will be propagated
            by this function.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command can be invoked.
        """
        cog = self.cog
        if cog is not None:
            local_check = type(cog)._get_overridden_method(cog.cog_check)
            if local_check is not None:
                ret = await utils.maybe_coroutine(local_check, ctx)
                if not ret:
                    return False

        predicates = self.checks
        if not predicates:
            # since we have no checks, then we just return True.
            return True

        return await utils.async_all(predicate(ctx) for predicate in predicates)  # type: ignore


    def to_dict(self) -> dict:            
        return {
            'name': self._name,
            'description': self._description,
            'type': self._type.value,
            'options': [option.to_dict() for option in self._options],
        }


class SlashCommandGroup(SlashCommandChild):
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

    This class inherits :class:`SlashCommandChild` so all attributes valid there are
    also valid in this class.
    """
    def __init__(self, callback: Callable, **attrs):
        super().__init__(
            callback,
            OptionType.sub_command_group,
            **attrs
        )
        self._children = []

    # parent attributes

    @property
    def children(self) -> List[SlashSubCommand]:
        """List[:class:`SlashSubCommand`]: The list of sub-commands this group has."""
        return self._children

    # children management

    def get_child(self, **attrs) -> Optional[SlashCommandChild]:
        """Gets a child that matches the provided traits.

        Parameters
        ----------
        **attrs:
            The attributes of the child.

        Returns
        -------
        Optional[:class:`SlashCommandChild`]
            The option that matched the traits. ``None`` if not found.
        """
        return utils.get(self._children, **attrs)

    def add_child(self, child: SlashCommandChild) -> SlashSubCommand:
        """Adds a child to this command.

        This is just a lower-level of :func:`SlashCommandGroup.sub_command` decorator.
        For general usage, Consider using it instead.

        Parameters
        ----------
        child: :class:`SlashCommandChild`
            The child to append.

        Returns
        -------
        :class:`SlashCommandChild`
            The appended child.
        """
        child._parent = self
        self._options.append(child)
        self._children.append(child)
        
        for opt in child.callback.__annotations__.values():
            if isinstance(opt, Option):
                child.append_option(opt)

        return child

    def remove_child(self, **attrs) -> Optional[SlashCommandChild]:
        """Removes a child from command that matches the provided traits.

        If child is not found, ``None`` would be returned.

        Parameters
        ----------
        **attrs:
            The attributes of the child.

        Returns
        -------
        Optional[:class:`SlashCommandChild`]
            The removed child. ``None`` if not found.
        """
        child = utils.get(self._children, **attrs)
        if child:
            self._children.remove(child)

        return child


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

        Parameters
        ----------
        **attrs:
            The parameters of :class:`SlashSubCommand`
        """
        def inner(func: Callable):
            return self.add_child(SlashSubCommand(func, **attrs))

        return inner



class SlashSubCommand(SlashCommandChild):
    """Represents a subcommand of a slash command.

    This can be registered using :func:`SlashCommand.sub_command` or
    :func:`SlashCommandGroup.sub_command` decorator.

    Example: ::

        @bot.slash_command(description='A cool command that has subcommands.')
        async def git(ctx):
            pass

        @git.sub_command(description='This is git push!')
        async def push(ctx):
            await ctx.send('Pushed!')

    The usage of above command would be like ``/git push``.

    This class inherits :class:`SlashCommandChild` so all attributes valid there are
    also valid in this class.
    """
    def __init__(self, callback: Callable, **attrs):
        super().__init__(
            callback,
            OptionType.sub_command.value,
            **attrs
        )
        self._parent: Union[SlashCommand, SlashCommandGroup] = None # type: ignore


    # Option management

    def get_option(self, **attrs) -> Optional[Option]:
        """Gets an option that matches the provided traits.

        Parameters
        ----------
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        Optional[:class:`Option`]
            The option that matched the traits. ``None`` if not found.
        """
        return utils.get(self._options, **attrs)

    def add_option(self, *, index: int = -1, **attrs) -> Option:
        """Adds an option to command.

        To append an option, Use :func:`SlashSubCommand.append_option`.

        Parameters
        ----------
        index: :class:`int`
            The index to insert at. Defaults to ``-1`` aka end of options list.
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        :class:`Option`
            The added option.
        """
        option = Option(**attrs)
        option._parent = self
        self._options.insert(index, option)
        return option

    def append_option(self, option: Option) -> Option:
        """Appends an option to end of options list.

        Parameters
        ----------
        option: :class:`Option`
            The option to append.

        Returns
        -------
        :class:`Option`
            The appended option.
        """
        option._parent = self
        self._options.append(option)
        return option

    def remove_option(self, **attrs) -> Optional[Option]:
        """Removes the option that matches the provided traits.

        If option is not found, ``None`` would be returned.

        Parameters
        ----------
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        Optional[:class:`Option`]
            The removed option. ``None`` if not found.
        """
        option = utils.get(self._options, **attrs)
        if option:
            self._options.remove(option)

        return option

SlashChildType = Union[
    Literal[OptionType.sub_command.value],
    Literal[OptionType.sub_command_group.value]
    ]


class SlashCommand(ApplicationCommand):
    """Represents a slash command.

    A slash command is a user input command that a user can use by typing ``/`` in
    the chat bar.

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The :attr:`SlashCommand.type` attribute will always be :attr:`ApplicationCommandType.slash`

    Attributes
    ----------
    type: :class:`ApplicationCommandType`
        The type of command, Always :attr:`ApplicationCommandType.slash`
    options: List[:class:`Option`]
        The list of options this command has.

        .. tip::
            To get only the children i.e sub-commands and sub-command groups,
            Consider using :attr:`children`

    children: List[:class:`SlashSubCommand`, `SlashCommandGroup`]
        The children of this commands i.e sub-commands and sub-command groups.
    """
    def __init__(self, callback, **attrs):
        self._type: ApplicationType = ApplicationCommandType.slash
        self._options: List[Option] = []
        self._children: List[SlashCommandChild] = []

        # To stay consistent with the discord.ext.commands models, I added this
        # parent attribute here which will always be None in case of this.
        # this is not documented for obvious reason.
        self.parent = None

        super().__init__(callback, **attrs)

    @property
    def type(self) -> ApplicationCommandType:
        """:class:`ApplicationCommandType`: The type of command. Always :attr:`ApplicatiionCommandType.slash`"""
        return self._type

    @property
    def options(self) -> List[Option]:
        """List[:class:`Option`]: The list of options this command has."""
        return self._options

    @property
    def children(self) -> List[Option]:
        """List[:class:`SlashSubCommand`, :class:`SlashCommandGroup`]: The list of children this command has."""
        return self._children

    # Option management

    def get_option(self, **attrs) -> Optional[Option]:
        """Gets an option that matches the provided traits.

        Parameters
        ----------
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        Optional[:class:`Option`]
            The option that matched the traits. ``None`` if not found.
        """
        return utils.get(self._options, **attrs)

    def add_option(self, *, index: int = -1, **attrs) -> Option:
        """Adds an option to command.

        To append an option, Use :func:`Option.append_option`.

        Parameters
        ----------
        index: :class:`int`
            The index to insert at. Defaults to ``-1`` aka end of options list.
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        :class:`Option`
            The added choice.
        """
        option = Option(**attrs)
        option._parent = self
        self._options.insert(index, option)
        return option

    def append_option(self, option: Option) -> Option:
        """Appends an option to end of options list.

        Parameters
        ----------
        option: :class:`Option`
            The option to append.

        Returns
        -------
        :class:`Option`
            The appended option.
        """
        option._parent = self
        self._options.append(option)
        return option

    def remove_option(self, **attrs) -> Optional[Option]:
        """Removes the option that matches the provided traits.

        If option is not found, ``None`` would be returned.

        Parameters
        ----------
        **attrs:
            The attributes of the :class:`Option`.

        Returns
        -------
        Optional[:class:`Option`]
            The removed choice. ``None`` if not found.
        """
        option = utils.get(self._options, **attrs)
        if option:
            self._options.remove(option)

        return option

    # children management

    def get_child(self, **attrs) -> Optional[SlashCommandChild]:
        """Gets a child that matches the provided traits.

        Parameters
        ----------
        **attrs:
            The attributes of the child.

        Returns
        -------
        Optional[:class:`SlashCommandChild`]
            The option that matched the traits. ``None`` if not found.
        """
        return utils.get(self._children, **attrs)

    def add_child(self, child: SlashCommandChild) -> SlashSubCommand:
        """Adds a child to this command.

        Parameters
        ----------
        child: :class:`SlashCommandChild`
            The child to append.

        Returns
        -------
        :class:`SlashCommandChild`
            The appended child.
        """
        child._parent = self
        self._options.append(child)
        self._children.append(child)

        for opt in child.callback.__annotations__.values():
            if isinstance(opt, Option):
                child.append_option(opt)

        return child

    def remove_child(self, **attrs) -> Optional[SlashCommandChild]:
        """Removes a child from command that matches the provided traits.

        If child is not found, ``None`` would be returned.

        Parameters
        ----------
        **attrs:
            The attributes of the child.

        Returns
        -------
        Optional[:class:`SlashCommandChild`]
            The removed child. ``None`` if not found.
        """
        child = utils.get(self._children, **attrs)
        if child:
            self._children.remove(child)

        return child


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
            return self.add_child(SlashSubCommand(func, **attrs))

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
            return self.add_child(SlashCommandGroup(func, **attrs))

        return inner

    def to_dict(self) -> dict:
        dict_ = {
            'name': self._name,
            'type': self._type.value,
            'options': [option.to_dict() for option in self.options],
            'description': self._description,
        }

        return dict_

class ContextMenuCommand(ApplicationCommand):
    """Represents a context menu command."""
    # This command is intentionally not documented

    def to_dict(self) -> dict:
        return {
            'name': self._name,
            'description': self._description,
            'type': self._type.value,
        }


class UserCommand(ApplicationCommand):
    """Represents a user command.

    A user command can be used by right-clicking a user in discord and choosing the
    command from "Apps" context menu

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.user`
    """
    def __init__(self, callback, **attrs):
        self._type = ApplicationCommandType.user
        super().__init__(callback, **attrs)

class MessageCommand(ApplicationCommand):
    """Represents a message command.

    A message command can be used by right-clicking a message in discord and choosing
    the command from "Apps" context menu.

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.message`
    """
    def __init__(self, callback, **attrs):
        self._type = ApplicationCommandType.message
        super().__init__(callback, **attrs)

def slash_option(name: str, type_: Any = None,  **attrs) -> Option:
    """A decorator-based interface to add options to a slash command.

    Usage: ::

        @bot.slash_command(description="Highfive a member!")
        @diskord.slash_option('member', description='The member to high-five.')
        @diskord.slash_option('reason', description='Reason to high-five')

        async def highfive(ctx, member: diskord.Member, reason = 'No reason!'):
            await ctx.send(f'{ctx.author.name} high-fived {member.name} for {reason}')

    .. warning::
        The callback function must contain the argument and properly annotated or TypeError
        will be raised.
    """
    def inner(func):
        nonlocal type_
        type_ = type_ or func.__annotations__.get(name, str)
        arg = attrs.pop('arg', name)

        sign = inspect.signature(func).parameters.get(arg)
        if sign is None:
            raise TypeError(f'Parameter for option {name} is missing.')

        required = attrs.pop('required', None)
        if required is None:
            required = sign.default is inspect._empty

        unwrap = unwrap_function(func)
        try:
            globalns = unwrap.__globals__
        except AttributeError:
            globalns = {}

        func.__application_command_params__ = get_signature_parameters(func, globalns)

        params = func.__application_command_params__
        type_ = params[arg].annotation

        if type_ is inspect._empty: # no annotations were passed.
            type_ = str

        func.__annotations__[arg] = Option(
            name=name,
            type=type_,
            arg=arg,
            required=required,
            callback=func,
            **attrs
            )
        return func

    return inner

def slash_command(**options) -> SlashCommand:
    """A decorator that converts a function to :class:`SlashCommand`

    Usage: ::

        @diskord.slash_command(description='My cool slash command.')
        async def test(ctx):
            await ctx.send('Hello world')
    """
    def inner(func: Callable):
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Callback function must be a coroutine.')

        options['name'] = options.get('name') or func.__name__

        return SlashCommand(func, **options)

    return inner

def user_command(**options) -> SlashCommand:
    """A decorator that converts a function to :class:`UserCommand`

    Usage: ::

        @diskord.user_command()
        async def test(ctx, user):
            await ctx.send('Hello world')
    """
    def inner(func: Callable):
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Callback function must be a coroutine.')
        options['name'] = options.get('name') or func.__name__

        return UserCommand(func, **options)

    return inner

def message_command(**options) -> SlashCommand:
    """A decorator that converts a function to :class:`MessageCommand`

    Usage: ::

        @diskord.message_command()
        async def test(ctx, message):
            await ctx.send('Hello world')
    """
    def inner(func: Callable):
        if not inspect.iscoroutinefunction(func):
            raise TypeError('Callback function must be a coroutine.')
        options['name'] = options.get('name') or func.__name__

        return MessageCommand(func, **options)

    return inner

def application_command_permission(*, guild_id: int, user_id: int = None, role_id: int = None, permission: bool = False):
    """A decorator that defines the permissions of :class:`ApplicationCommand`

    Usage: ::

        @bot.slash_command(guild_ids=[12345], description='Cool command')
        @diskord.application_command_permission(guild_id=12345, user_id=1234, permission=False)
        @diskord.application_command_permission(guild_id=12345, role_id=123456, permission=True)
        async def command(ctx):
            await ctx.send('Hello world')

    In above command, The user with ID ``1234`` would not be able to use to command
    and anyone with role of ID ``123456`` will be able to use the command in the guild
    with ID ``12345``.
    """
    def inner(func: Callable[..., Any]):
        if not hasattr(func, '__application_command_permissions__'):
            func.__application_command_permissions__ = []

        if user_id is not None and role_id is not None:
            raise TypeError('keyword paramters user_id and role_id cannot be mixed.')

        if user_id is not None:
            id = user_id
            type = ApplicationCommandPermissionType.user

        elif role_id is not None:
            id = role_id
            type = ApplicationCommandPermissionType.role


        found = False
        for perm in func.__application_command_permissions__:
            if perm.guild_id == guild_id:
                found = True
                perm._permissions.append(
                    ApplicationCommandPermission(
                        id=id,
                        type=type,
                        permission=permission,
                    )
                )

        if not found:
            func.__application_command_permissions__.append(
                ApplicationCommandGuildPermissions(
                    guild_id=guild_id,
                    application_id=None, # type: ignore
                    command_id=None, # type: ignore
                    permissions=[
                        ApplicationCommandPermission(
                            id=id,
                            type=type,
                            permission=permission,
                        )
                    ]
                )
            )
        return func

    return inner