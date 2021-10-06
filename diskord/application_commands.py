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
from .utils import unwrap_function, get_signature_parameters
from .enums import (
    try_enum,
    ApplicationCommandType,
    OptionType,
    ApplicationCommandPermissionType,
)
from .errors import (
    ApplicationCommandError,
    ApplicationCommandCheckFailure,
    ApplicationCommandConversionError,
)
from .user import User
from .member import Member
from .message import Message
from .interactions import InteractionContext

if TYPE_CHECKING:
    from .types.interactions import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
        ApplicationCommandPermissions as ApplicationCommandPermissionsPayload,
    )

__all__ = (
    "PartialApplicationCommand",
    "ApplicationCommand",
    "ApplicationCommandGuildPermissions",
    "ApplicationCommandPermission",
    "SlashCommand",
    "SlashCommandChild",
    "SlashSubCommand",
    "SlashCommandGroup",
    "UserCommand",
    "MessageCommand",
    "Option",
    "OptionChoice",
    "slash_option",
    "slash_command",
    "user_command",
    "message_command",
    "application_command_permission",
)

### --- Types Start --- ###

Check = Callable[[InteractionContext, "Context"], bool]

### --- Types End --- ###


### --- Mixins Start --- ###


class ChildrenMixin:
    """A mixin that implements children for slash commands or slash subcommand groups.

    This is not meant to be initalized manually and is here for documentation purposes.
    """

    @property
    def children(self) -> List[SlashSubCommand]:
        """List[:class:`SlashSubCommand`]: The list of sub-commands this group has."""
        return self._children

    def get_child(self, **attrs: Any) -> Optional[SlashCommandChild]:
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

        if not hasattr(child.callback, "__application_command_params__"):
            child.callback.__application_command_params__ = {}

        for opt in child.callback.__application_command_params__.values():
            child.append_option(opt)

        return child

    def remove_child(self, **attrs: Any) -> Optional[SlashCommandChild]:
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


class OptionsMixin:
    """A mixin that implements basic slash commands and subcommands options."""

    @property
    def options(self):
        return self._options

    # Option management

    def get_option(self, **attrs: Any) -> Optional[Option]:
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

    def add_option(self, index: int = -1, **attrs: Any) -> Option:
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

    def remove_option(self, **attrs: Any) -> Optional[Option]:
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


class ChecksMixin:
    """A mixin that implements checks for application commands."""

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
        inside the :attr:`~ApplicationCommand.checks` attribute.

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
        if hasattr(ctx.bot, "can_run"):
            if not await ctx.bot.can_run(ctx):
                raise ApplicationCommandCheckFailure(
                    f"The global check functions for command {self.qualified_name} failed."
                )

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


### --- Mixins End --- ###


### --- Options Start --- ###


class OptionChoice:
    """Represents an option choice for an application command's option.

    Attributes
    ----------

    name: :class:`str`
        The name of choice. Will be shown on command explorer.
    value: :class:`str`
        A user-set value of the choice. Will be passed in the command's callback.
    """

    def __init__(self, *, name: str, value: Union[str, int, float]):
        self.name = name
        self.value = value

        self._option: Option = None  # type: ignore

    @property
    def option(self) -> Option:
        """:class:`Option`: The parent option of this choice."""
        return self._option

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, dict_: ApplicationCommandOptionChoicePayload):
        return cls(name=dict_["name"], value=dict_["value"])

    def __repr__(self):
        return f"<OptionChoice name={self.name!r} value={self.value!r}>"

    def __str__(self):
        return self.name


class Option:
    """Represents an option for an application slash command.

    This class is generally not initialized manually, Instead :func:`.option` decorator
    interface is used.

    .. note::
        All parameters except :attr:`Option.name` are optional.

    Parameters
    ----------
    name: :class:`str`
        The name of option.
    description: :class:`str`
        The description of option. Defaults to ``No description``
    type: :class:`OptionType`
        The type of the option. Defaults to :attr:`OptionType.string`
        While using :func:`.slash_option` decorator, This is determined by type or annotation
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
    autocomplete:
        The function that would autocomplete this option if applicable.
        If option does not has autocompletion, then this is ``None``.
        
        First parameter of function would represent the value of option that
        is focused and second parameter is the autocompletion :class:`~diskord.Interaction`.

        This function must be a coroutine.

        Example: ::
            
            async def autocomplete(value, interaction):
                data = {
                    'Bun': 'bun',
                    'Cookie': 'cookie',
                    'Cake': 'cake',
                }
                return [
                    diskord.OptionChoice(name=name, value=data[name])
                    for name in data if name.startswith(value)
                    ]

            @bot.slash_command()
            @diskord.slash_option('item', autocomplete=autocomplete)
            async def buy(ctx, item):
                await ctx.send(f'You bought {item}')

    """

    def __init__(
        self,
        *,
        name: str,
        description: str = None,
        type: OptionType = str,
        choices: List[OptionChoice] = None,
        required: bool = True,
        arg: str = None,
        converter: "Converter" = None,
        autocomplete: Callable[[str], List[OptionChoice]] = None,
        **attrs,
    ):
        self.callback: Callable[..., Any] = attrs.get("callback")
        self._name = name
        self._description = description or "No description"
        self._required = required
        self._channel_types: List[ChannelType] = attrs.get("channel_types", [])  # type: ignore
        self._choices: List[OptionChoice] = choices
        self._options: List[Option] = []
        self.autocomplete: Callable[[str], List[OptionChoice]] = autocomplete
        
        if self._choices is None:
            self._choices = []

        self.arg = arg or self.name
        self.converter: "Converter" = converter  # type: ignore

        self._parent: Union[ApplicationCommand, Option] = None  # type: ignore

        if type in [OptionType.sub_command_group, OptionType.sub_command]:
            self._type = type
        else:
            try:
                self._type: OptionType = OptionType.from_datatype(type, option=self)
            except TypeError:
                self._type: OptionType = type

    def __repr__(self):
        return f"<Option name={self._name!r} description={self._description!r}>"

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

        .. note::
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

    def add_choice(self, index: int = -1, **attrs) -> OptionChoice:
        """Adds a choice to option.

        To append a choice, Use :func:`Option.append_choice`.

        Parameters
        ----------
        index: :class:`int`
            The position to insert the choice at.
        name: :class:`str`
            The name of choice. Will be shown on command explorer.
        value: :class:`str`
            A user-set value of the choice. Will be passed in the command's callback.

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

    def remove_choice(self, **attrs: Any) -> Optional[OptionChoice]:
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

    def get_option(self, **attrs: Any) -> Optional[Option]:
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

    def add_option(self, index: int = -1, **attrs: Any) -> Option:
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

    def remove_option(self, **attrs: Any) -> Optional[Option]:
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

    def is_command_or_group(self) -> bool:
        """:class:`bool`: Indicates whether this option is a subcommand or subgroup."""
        return self._type.value in (
            OptionType.sub_command.value,
            OptionType.sub_command_group.value,
        )

    def can_autocomplete(self) -> bool:
        """:class:`bool`: Indicates whether this option can autocomplete or not."""
        return (self.autocomplete is not None)

    def to_dict(self) -> dict:
        dict_ = {
            "type": self._type.value,
            "name": self._name,
            "description": self._description,
            "choices": [choice.to_dict() for choice in self._choices],
            "options": [option.to_dict() for option in reversed(self.options)],
            "autocomplete": self.can_autocomplete(),
        }

        if not self.is_command_or_group():
            # Discord API doesn't allow passing required in the payload of
            # options that have type of 1 or 2.
            dict_["required"] = self._required

        if self._channel_types:
            dict_["channel_types"] = []
            for t in self._channel_types:
                if isinstance(t, list):
                    for st in t:
                        dict_["channel_types"].append(st.value)
                else:
                    dict_["channel_types"].append(t.value)

        return dict_


### --- Options End --- ###


### --- Application Command Permissions Start --- ###


class ApplicationCommandGuildPermissions:
    """Represents the permissions for an application command in a :class:`Guild`.

    Application commands permissions allow you to restrict an application command
    to a certain roles or users.

    Attributes
    ----------
    permissions: List[:class:`ApplicationCommandGuildPermissions`]
        The list that the commands hold in the guild.
    """

    def __init__(
        self,
        *,
        command_id: int,
        application_id: int,
        guild_id: int,
        permissions: List[ApplicationCommandPermission],
    ):
        self._command_id = command_id
        self._application_id = application_id
        self._guild_id = guild_id
        self._permissions = permissions

        self._command: ApplicationCommand = None  # type: ignore

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
            "command_id": self._command_id,
            "application_id": self._application_id,
            "guild_id": self._guild_id,
            "permissions": [perm.to_dict() for perm in self._permissions],
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

    def __init__(
        self, *, id: int, type: ApplicationCommandPermissionType, permission: bool
    ):
        self.id = id
        self.type = type
        self.permission = bool(permission)

    def to_dict(self):
        ret = {
            "id": self.id,
            "permission": self.permission,
            "type": self.type.value,
        }

        return ret


### --- Application Command Permissions End --- ###


### --- Application Commands Start --- ###


class PartialApplicationCommand:
    """Represents a *partial* application command.

    This class is usually returned by API calls or under circumstances when the
    application command is not found in cache. Unlike :class:`.ApplicationCommand`
    This class doesn't has any ``callback`` attribute.

    Attributes
    ----------
    name: :class:`str`
        The name of application command.
    description: :class:`str`
        The description of application command.
    guild_id: :class:`int`
        The ID of guild this command belongs to, ``None`` if command
        is a global command.
    default_permission: :class:`bool`
        The command's default permission.
    id: :class:`int`
        The unique ID of this command.
    version: :class:`int`
        The auto incrementing version of this application command.
    application_id: :class:`int`
        The ID of application this command belongs to.
    """

    def __init__(self, data: ApplicationCommandPayload, client: Client = None):
        self._client = self._bot = client
        self._from_data(data)

    def _ensure_state(self):
        if self._client:
            self._state = self._client._connection

    def _from_data(self, data: ApplicationCommandPayload) -> ApplicationCommand:
        self._id: int = utils._get_as_snowflake(data, "id")
        self._application_id: int = utils._get_as_snowflake(data, "application_id")
        self._guild_id: int = utils._get_as_snowflake(data, "guild_id")
        self._version: int = utils._get_as_snowflake(data, "version")
        self._default_permission = data.get("default_permission", getattr(self, "default_permission", True))  # type: ignore

        if "name" in data:
            self._name = data.get("name")
        if "description" in data:
            self._description = data.get("description")

        self._ensure_state()
        return self

    @property
    def name(self) -> str:
        """:class:`str`: The name of application command."""
        return self._name

    @property
    def description(self) -> str:
        """:class:`description`: The description of application command."""
        return self._description

    @property
    def guild_id(self) -> int:
        """:class:`int`: The ID of the guild this command belongs to.

        Every command is stored per-guild basis and this attribute represents that guild's ID.
        To get the list of guild IDs in which this command was initially registered, use
        :attr:`ApplicationCommand.guild_id`
        """
        return self._guild_id

    @property
    def guild(self) -> Optional[Guild]:
        """:class:`Guild`: The guild this command belongs to. This could be ``None`` if command is a global command."""
        if self._client:
            return self._client.get_guild(self.guild_id)

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

    async def edit(
        self,
        *,
        name: str = None,
        description: str = None,
        options: List[Option] = None,
        default_permission: bool = None,
    ):
        """|coro|

        Edits the application command.

        .. note::
            If the command is a global command, Then updates would
            take upto 1 hour to take affect in all guilds. Updates
            for guilds commands is instant.

        Parameters
        ----------

        name: :class:`str`
            The new name of application command.
        description: :class:`str`
            The new description of application command.
        options: :class:`Option`
            The new options parameters of this command.
        default_permission: :class:`bool`
            The new default permission of the application command.
            Setting this to ``False`` will disable the command by default
            unless a permission overwrite is configured.

        Returns
        -------
        :class:`ApplicationCommand`:
            The updated command
        """
        payload: Dict[str, Any] = {}

        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if options is not None:
            payload["options"] = [option.to_dict() for option in options]
        if default_permission is not None:
            payload["default_permission"] = bool(default_permission)

        if self.guild_id:
            ret = await self._state.http.edit_guild_command(
                command_id=self.id,
                guild_id=self.guild_id,
                application_id=self._state.user.id,
                payload=payload,
            )
        else:
            ret = await self._state.http.edit_global_command(
                command_id=self.id,
                application_id=self._state.user.id,
                payload=payload,
            )

        return self._from_data(ret)

    async def delete(self):
        """|coro|

        Deletes the application command. This function also removes the command
        from internal cache of application commands.
        """
        if self.guild_id:
            ret = await self._client._connection.http.delete_guild_command(
                command_id=self.id,
                guild_id=self.guild_id,
                application_id=self._state.user.id,
            )
        else:
            ret = await self._client._connection.http.delete_global_command(
                command_id=self.id,
                application_id=self._state.user.id,
            )

        self._state._application_commands.pop(self.id, None)  # type: ignore


class ApplicationCommand(PartialApplicationCommand, ChecksMixin):
    """Represents an application command.

    This is base class for all application commands like slash commands,
    user commands and message commands etc.

    Attributes
    ----------
    checks: List[Callable[:class:`InteractionContext`, bool]]
        The list of checks this commands holds that will be checked before command's
        invocation.

        For more info on checks and how to register them, See :func:`~ext.commands.check`
        documentation as these checks actually come from there.
    extras: :class:`dict`
        A dict of user provided extras to attach to the Command.
    """

    def __init__(self, callback: Callable, **attrs: Any):
        self._callback = callback
        self._guild_ids = attrs.pop("guild_ids", [])
        self._description = (
            attrs.pop("description", callback.__doc__) or "No description"
        )
        self._name = attrs.pop("name", callback.__name__)
        self._default_permission = attrs.pop("default_permission", True)
        self.extras: Dict[str, Any] = attrs.pop("extras", {})

        self._cog = None
        self._client = self._bot = None

        super().__init__(dict(), self._client)
        self._update_callback_data()

    def is_global_command(self) -> bool:
        """:class:`bool`: Whether the command is global command or not."""
        return bool(self._guild_ids)

    def _update_callback_data(self):
        try:
            permissions = self.callback.__application_command_permissions__
        except AttributeError:
            permissions = []  # type: ignore

        for perm in permissions:
            perm._command = self

        self.checks: List[Check]
        try:
            self.checks = self.callback.__commands_checks__
            self.checks.reverse()
        except AttributeError:
            self.checks = []

        self._permissions: List[ApplicationCommandGuildPermissions] = permissions

    @property
    def callback(self) -> Callable[..., Any]:
        """Returns the callback function that this command holds."""
        return self._callback

    @callback.setter
    def callback(self, value) -> None:
        self._callback = value

        if not hasattr(value, "__application_command_params__"):
            value.__application_command_params__ = {}

        self._options = []

        for opt in value.__application_command_params__.values():
            self.append_option(opt)

        self._update_callback_data()

    @property
    def permissions(self) -> List[ApplicationCommandGuildPermissions]:
        """List[:class:`ApplicationCommandGuildPermissions`]: List of permissions this command holds."""
        return self._permissions

    @property
    def guild_ids(self) -> List[int]:
        """List[:class:`int`]: The list of guild IDs in which this command will/was register.

        Unlike :attr:`ApplicationCommand.guild_id` this is the list of guild IDs in which command
        will register on the bot's connect.
        """
        return self._guild_ids

    @property
    def cog(self):
        """
        Optional[:class:`ext.commands.Cog`]: Returns the cog in which this command was
        registered. If command has no cog, then ``None`` is returned.
        """
        return self._cog

    def __repr__(self):
        # More attributes here?
        return f"<ApplicationCommand name={self.name!r} description={self.description!r} guild_ids={self.guild_ids!r}"

    def __str__(self):
        return self.name


### --- Application Commands End --- ###


### --- Context Menu Commands Start --- ###


class ContextMenuCommand(ApplicationCommand):
    """Represents a context menu command."""

    # This class is intentionally not documented

    def __init__(self, callback: Callable[..., Any], **attrs: Any):
        super().__init__(callback, **attrs)
        self._description = ""

    def to_dict(self) -> dict:
        return {
            "name": self._name,
            "description": self._description,
            "type": self._type.value,
        }


class UserCommand(ContextMenuCommand):
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

    async def invoke(self, context: InteractionContext):
        """|coro|

        Invokes the user command with provided invocation context.

        Parameters
        ----------
        context: :class:`InteractionContext`
            The interaction invocation context.
        """
        context.command = self
        interaction: Interaction = context.interaction
        args = [context]

        if not interaction.data["type"] == self.type.value:
            raise TypeError(
                f'interaction type does not matches the command type. Interaction type is {interaction.data["type"]} and command type is {self.type}'
            )

        resolved = interaction.data["resolved"]
        if interaction.guild:
            member_with_user = resolved["members"][interaction.data["target_id"]]
            member_with_user["user"] = resolved["users"][interaction.data["target_id"]]
            user = Member(
                data=member_with_user,
                guild=interaction.guild,
                state=interaction.guild._state,
            )
        else:
            user = User(
                state=context.client._connection,
                data=resolved["users"][interaction.data["target_id"]],
            )

        args.append(user)

        if context.command.cog is not None:
            args.insert(0, context.command.cog)

        self._bot.dispatch('application_command_run', context)
        await context.command.callback(*args)


class MessageCommand(ContextMenuCommand):
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

    async def invoke(self, context: InteractionContext):
        """|coro|

        Invokes the message command with provided invocation context.

        Parameters
        ----------
        context: :class:`InteractionContext`
            The interaction invocation context.
        """
        context.command = self
        interaction: Interaction = context.interaction
        args = [context]

        if not interaction.data["type"] == self.type.value:
            raise TypeError(
                f'interaction type does not matches the command type. Interaction type is {interaction.data["type"]} and command type is {self.type}'
            )

        data = interaction.data["resolved"]["messages"][interaction.data["target_id"]]
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

        if context.command.cog is not None:
            args.insert(0, context.command.cog)

        self._bot.dispatch('application_command_run', context)
        await context.command.callback(*args)


### --- Context Menu Commands End --- ###


### --- Slash Commands Start --- ###


class SlashCommand(ApplicationCommand, ChildrenMixin, OptionsMixin):
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

    children: List[:class:`.SlashCommandChild`]
        The children of this commands i.e sub-commands and sub-command groups.
    """

    def __init__(self, callback, **attrs: Any):
        self._type: ApplicationType = ApplicationCommandType.slash
        self._options: List[Option] = []
        self._children: List[SlashCommandChild] = []

        super().__init__(callback, **attrs)

    @property
    def type(self) -> ApplicationCommandType:
        """:class:`ApplicationCommandType`: The type of command. Always :attr:`ApplicatiionCommandType.slash`"""
        return self._type

    async def _parse_option(
        self, interaction: Interaction, option: ApplicationCommandOptionPayload
    ) -> Any:
        # This function isn't needed to be a coroutine function but it can be helpful in
        # future so, yes that's the reason it's an async function.

        if option["type"] in (
            OptionType.string.value,
            OptionType.integer.value,
            OptionType.boolean.value,
            OptionType.number.value,
        ):
            value = option["value"]

        elif option["type"] == OptionType.user.value:
            if interaction.guild:
                value = interaction.guild.get_member(int(option["value"]))
            else:
                value = context.client.get_user(int(option["value"]))

            # value can be none in case when member intents are not available

            if value is None:
                resolved = interaction.data["resolved"]
                if interaction.guild:
                    member_with_user = resolved["members"][option["value"]]
                    member_with_user["user"] = resolved["users"][option["value"]]
                    value = Member(
                        data=member_with_user,
                        guild=interaction.guild,
                        state=interaction.guild._state,
                    )
                else:
                    value = User(
                        state=context.client._connection,
                        data=resolved["users"][option["value"]],
                    )

        elif option["type"] == OptionType.channel.value:
            value = interaction.guild.get_channel(int(option["value"]))

        elif option["type"] == OptionType.role.value:
            value = interaction.guild.get_role(int(option["value"]))

        elif option["type"] == OptionType.mentionable.value:
            value = interaction.guild.get_member(
                int(option["value"])
            ) or interaction.guild.get_role(int(option["value"]))

        return value

    async def _run_converter(self, converter, ctx, value):
        try:
            converted = await converter().convert(ctx, value)
        except Exception as error:
            if isinstance(error, ApplicationCommandError):
                raise error
            raise ApplicationCommandConversionError(converter, error) from error
        else:
            return converted

    async def invoke(self, context: InteractionContext):
        """|coro|

        Invokes the slash command or subcommand from provided interaction invocation context.

        Parameters
        ----------

        context: :class:`InteractionContext`
            The interaction invocation context.
        """
        interaction: Interaction = context.interaction
        args = [context]

        if not interaction.data["type"] == self.type.value:
            raise TypeError(
                f'interaction type does not matches the command type. Interaction type is {interaction.data["type"]} and command type is {self.type}'
            )

        options = interaction.data.get("options", [])
        kwargs = {}

        for option in options:
            if option["type"] == OptionType.sub_command.value:
                # We will use the name to get the child because
                # subcommands do not have any ID. They are essentially
                # just options of a command. And option names are unique

                subcommand = self.get_child(name=option["name"])
                context.command = subcommand

                if not (await context.command.can_run(context)):
                    raise ApplicationCommandCheckFailure(
                        f"checks functions for application command {context.command._name} failed."
                    )

                sub_options = option.get("options", [])

                for sub_option in sub_options:
                    value = await self._parse_option(interaction, sub_option)
                    resolved = subcommand.get_option(name=sub_option["name"])
                    if resolved.converter is not None:
                        converted = await self._run_converter(
                            resolved.converter, context, value
                        )
                        kwargs[resolved.arg] = converted
                    else:
                        kwargs[resolved.arg] = value

            elif option["type"] == OptionType.sub_command_group.value:
                # In case of sub-command groups interactions, The options array
                # only has one element which is the subcommand that is being used
                # so we essentially just have to get the first element of the options
                # list and lookup the callback function for name of that element to
                # get the subcommand object.

                subcommand_raw = option["options"][0]
                group = self.get_child(name=option["name"])
                subcommand = group.get_child(name=subcommand_raw["name"])
                context.command = subcommand

                if not (await context.command.can_run(context)):
                    raise ApplicationCommandCheckFailure(
                        f"checks functions for application command {context.command._name} failed."
                    )

                sub_options = subcommand_raw.get("options", [])

                for sub_option in sub_options:
                    value = await self._parse_option(interaction, sub_option)
                    resolved = subcommand.get_option(name=sub_option["name"])

                    if resolved.converter is not None:
                        converted = await self._run_converter(
                            resolved.converter, context, value
                        )
                        kwargs[resolved.arg] = converted
                    else:
                        kwargs[resolved.arg] = value

            else:
                value = await self._parse_option(interaction, option)
                resolved = self.get_option(name=option["name"])

                if resolved.converter is not None:
                    converted = await self._run_converter(
                        resolved.converter, context, value
                    )
                    kwargs[resolved.arg] = converted
                else:
                    kwargs[resolved.arg] = value

        if context.command is None:
            context.command = self

        if not (await context.command.can_run(context)):
            raise ApplicationCommandCheckFailure(
                f"checks functions for application command {context.command._name} failed."
            )

        if context.command.cog is not None:
            args.insert(0, context.command.cog)

        self._bot.dispatch('application_command_run', context)
        await context.command.callback(*args, **kwargs)

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
                await ctx.respond('Pushed!')

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
                await ctx.respond('Hello world!')
        """

        def inner(func: Callable):
            return self.add_child(SlashCommandGroup(func, **attrs))

        return inner

    def to_dict(self) -> dict:
        dict_ = {
            "name": self._name,
            "type": self._type.value,
            "options": [option.to_dict() for option in reversed(self.options)],
            "description": self._description,
        }

        return dict_


class SlashCommandChild(SlashCommand):
    """
    Base class for slash commands children. Current examples are

    * :class:`SlashCommandGroup`
    * :class:`SlashSubCommand`

    This class subclasses :class:`SlashCommand` so all attributes of option class are valid here.

    This class is not meant to be initalized manually and is here for documentation-purposes only.
    For general use, Use the subclasses of this class like  :class:`SlashCommandGroup` and
    :class:`SlashSubCommand`.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._parent: SlashCommand = None  # type: ignore

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

    def to_dict(self) -> dict:
        return {
            "name": self._name,
            "description": self._description,
            "type": self._type.value,
            "options": [option.to_dict() for option in reversed(self.options)],
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
            await ctx.respond('Permissions cleared!')


    In above example, ``/permissions`` is a slash command and ``role`` is a subcommand group
    in that slash command that holds command ``clear`` to use the ``clear`` command, The
    command will be ``/permissions role clear``.

    More command groups can be added in a slash command and similarly, more commands
    can be added into a group.

    This class inherits :class:`SlashCommandChild` so all attributes valid there are
    also valid in this class.
    """

    def __init__(self, callback: Callable, **attrs: Any):
        super().__init__(callback, **attrs)
        self._type = OptionType.sub_command_group
        self._children: List[SlashCommandChild] = []

    # decorators

    def sub_command(self, **attrs: Any):
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
                await ctx.respond('Hello world!')

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
            await ctx.respond('Pushed!')

    The usage of above command would be like ``/git push``.

    This class inherits :class:`SlashCommandChild` so all attributes valid there are
    also valid in this class.
    """

    def __init__(self, callback: Callable, **attrs: Any):
        super().__init__(callback, **attrs)
        self._type = OptionType.sub_command


### --- Slash Commands End --- ###


### --- Decorators Start --- ###


def slash_option(name: str, **attrs) -> Option:
    """A decorator-based interface to add options to a slash command.

    Usage: ::

        @bot.slash_command(description="Highfive a member!")
        @diskord.slash_option('member', description='The member to high-five.')
        @diskord.slash_option('reason', description='Reason to high-five')

        async def highfive(ctx, member: diskord.Member, reason = 'No reason!'):
            await ctx.respond(f'{ctx.author.name} high-fived {member.name} for {reason}')

    .. warning::
        The callback function must contain the argument and properly annotated or TypeError
        will be raised.
    """

    def inner(func):
        # Originally the Option object was inserted directly in
        # annotations but that was problematic so it was changed to
        # this.

        arg = attrs.pop("arg", name)

        if not hasattr(func, "__application_command_params__"):
            func.__application_command_params__ = {}

        unwrap = unwrap_function(func)
        try:
            globalns = unwrap.__globals__
        except AttributeError:
            globalns = {}

        params = get_signature_parameters(func, globalns)
        param = params.get(arg)

        required = attrs.pop("required", None)
        if required is None:
            required = param.default is inspect._empty

        type = params[arg].annotation

        if type is inspect._empty:  # no annotations were passed.
            type = str

        func.__application_command_params__[arg] = Option(
            name=name, type=type, arg=arg, required=required, callback=func, **attrs
        )
        return func

    return inner


def slash_command(**options) -> SlashCommand:
    """A decorator that converts a function to :class:`SlashCommand`

    Usage: ::

        @diskord.slash_command(description='My cool slash command.')
        async def test(ctx):
            await ctx.respond('Hello world')
    """

    def inner(func: Callable):
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Callback function must be a coroutine.")

        options["name"] = options.get("name") or func.__name__

        return SlashCommand(func, **options)

    return inner


def user_command(**options) -> SlashCommand:
    """A decorator that converts a function to :class:`UserCommand`

    Usage: ::

        @diskord.user_command()
        async def test(ctx, user):
            await ctx.respond('Hello world')
    """

    def inner(func: Callable):
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Callback function must be a coroutine.")
        options["name"] = options.get("name") or func.__name__

        return UserCommand(func, **options)

    return inner


def message_command(**options) -> SlashCommand:
    """A decorator that converts a function to :class:`MessageCommand`

    Usage: ::

        @diskord.message_command()
        async def test(ctx, message):
            await ctx.respond('Hello world')

    Parameters
    ----------
    **options:
        The options of :class:`MessageCommand`
    """

    def inner(func: Callable):
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Callback function must be a coroutine.")
        options["name"] = options.get("name") or func.__name__

        return MessageCommand(func, **options)

    return inner


def application_command_permission(
    *, guild_id: int, user_id: int = None, role_id: int = None, permission: bool = False
):
    """A decorator that defines the permissions of :class:`ApplicationCommand`

    Usage: ::

        @bot.slash_command(guild_ids=[12345], description='Cool command')
        @diskord.application_command_permission(guild_id=12345, user_id=1234, permission=False)
        @diskord.application_command_permission(guild_id=12345, role_id=123456, permission=True)
        async def command(ctx):
            await ctx.respond('Hello world')

    In above command, The user with ID ``1234`` would not be able to use to command
    and anyone with role of ID ``123456`` will be able to use the command in the guild
    with ID ``12345``.
    """

    def inner(func: Callable[..., Any]):
        if not hasattr(func, "__application_command_permissions__"):
            func.__application_command_permissions__ = []

        if user_id is not None and role_id is not None:
            raise TypeError("keyword paramters user_id and role_id cannot be mixed.")

        if user_id is not None:
            id = user_id
            type = ApplicationCommandPermissionType.user

        elif role_id is not None:
            id = role_id
            type = ApplicationCommandPermissionType.role

        for perm in func.__application_command_permissions__:
            if perm.guild_id == guild_id:
                perm._permissions.append(
                    ApplicationCommandPermission(
                        id=id,
                        type=type,
                        permission=permission,
                    )
                )
                return func

        func.__application_command_permissions__.append(
            ApplicationCommandGuildPermissions(
                guild_id=guild_id,
                application_id=None,  # type: ignore
                command_id=None,  # type: ignore
                permissions=[
                    ApplicationCommandPermission(
                        id=id,
                        type=type,
                        permission=permission,
                    )
                ],
            )
        )
        return func

    return inner


### --- Decorators End --- ###
