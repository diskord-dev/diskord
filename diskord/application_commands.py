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
from itertools import filterfalse
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Callable,
    Union,
)

from .utils import _get_as_snowflake
from .enums import (
    ApplicationCommandType,
    ApplicationCommandPermissionType,
    OptionType,
    ChannelType,
    try_enum,
)

if TYPE_CHECKING:
    from .types.interactions import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        GuildApplicationCommandPermissions as GuildApplicationCommandPermissionsPayload,
    )
    from .state import ConnectionState
    from .guild import Guild

__all__ = (
    "ApplicationCommand",
    "ApplicationCommandOption",
    "OptionChoice",
    "ApplicationSlashCommand",
    "ApplicationUserCommand",
    "ApplicationMessageCommand",
    "ApplicationCommandGuildPermissions",
    "ApplicationCommandPermission",
)

class ApplicationCommandGuildPermissions:
    """
    Represents the permissions for an application command in a :class:`Guild`.

    Application commands permissions allow you to restrict an application command
    to a certain roles or users in a specific Guild.

    This class is not user construct-able, Use :class:`application.ApplicationCommandPermissions`
    instead to create custom permissions.
    """
    __slots__ = ('_command_id', '_application_id', '_guild_id', '_permissions', '_state')

    def __init__(self, data: GuildApplicationCommandPermissionsPayload, state: ConnectionState):
        self._command_id: int = int(data['id'])
        self._application_id: int = int(data['application_id'])
        self._guild_id: int = int(data['guild_id'])
        self._permissions: List[ApplicationCommandPermission] = [ApplicationCommandPermission(perm) for perm in data.get('permissions', [])] # type: ignore

        self._state: ConnectionState = state

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

    @property
    def guild(self) -> Optional[Guild]:
        """:class:`Guild`: Returns the guild that the permissions belong to, if available."""
        return self._state._get_guild(self.guild_id)

    @property
    def permissions(self) -> ApplicationCommandPermission:
        """List[:class:`ApplicationCommandPermission`]: The list of permissions that are configured."""
        return self._permissions


class ApplicationCommandPermission:
    """A class representing a specific permission for an application command.

    .. note::
        This class is not user constructable, Use :class:`application.CommandPermissionOverwrite`
        instead.

    Attributes
    ----------

    id: :class:`int`
        The ID of role or user whose permission is being defined.
    type: :class:`ApplicationCommandPermissionType`
        The type of entity of which permission is being defined.
    permission: :class:`bool`
        The permission for the command. If this is set to ``False`` the provided
        user or role will not be able to use the command. Defaults to ``False``
    """
    __slots__ = ('id', 'type', 'permission')

    def __init__(self, data):
        self.id = int(data['id'])
        self.type: ApplicationCommandPermissionType = try_enum(ApplicationCommandPermissionType, int(data['type']))
        self.permission = data['permission']


class ApplicationCommandMixin:
    if TYPE_CHECKING:
        _state: ConnectionState
        _guild_id: int
        _id: int
        _application_id: int
        _version: int
        _name: str
        _description: str
        _default_permission: bool
        _type: ApplicationCommandType

    async def _edit_permissions(self, permissions: ApplicationCommandPermissions):
        user = self._state._get_client().user
        permissions.command = self
        permissions_payload = {'permissions': [perm.to_dict() for perm in permissions.overwrites]}

        data = await self._state.http.edit_application_command_permissions(
            application_id=user.id,
            guild_id=permissions.guild_id,
            command_id=self.id,
            payload=permissions_payload
        )
        return data

    async def edit(
        self,
        *,
        name: str = None,
        description: str = None,
        options: List[Option] = None, # type: ignore
        default_permission: bool = None,
        permissions: ApplicationCommandPermissions = None,
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
        permissions: :class:`application.ApplicationCommandPermissions`
            The new permissions of the command in a specific guild.

        Returns
        -------
        :class:`ApplicationCommand`:
            The updated command
        """
        user = self._state._get_client().user

        if permissions is not None:
            await self._edit_permissions(permissions)

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
                application_id=user.id,
                payload=payload,
            )
        else:
            ret = await self._state.http.edit_global_command(
                command_id=self.id,
                application_id=user.id,
                payload=payload,
            )

        return self._from_data(ret)

    async def delete(self):
        """|coro|

        Deletes the application command.
        """
        if self.guild_id:
            ret = await self._state.http.delete_guild_command(
                command_id=self.id,
                guild_id=self.guild_id,
                application_id=self._state.user.id,
            )
        else:
            ret = await self._state.http.delete_global_command(
                command_id=self.id,
                application_id=self._state.user.id,
            )

        self._state._commands_store.remove_application_command(self.id)  # type: ignore

    def _from_data(self, data: ApplicationCommandPayload):
        self._id: int = _get_as_snowflake(data, "id")
        self._application_id: int = _get_as_snowflake(data, "application_id")
        self._guild_id: int = _get_as_snowflake(data, "guild_id")
        self._version: int = _get_as_snowflake(data, "version")
        self._default_permission = data.get("default_permission", getattr(self, "_default_permission", True))  # type: ignore
        self._name = data.get("name", getattr(self, '_name', None))
        self._description = data.get("description", getattr(self, '_description', None))
        self._type = try_enum(ApplicationCommandType, int(data['type'])) # type: ignore
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
        if self._state:
            return self._state._get_guild(self.guild_id)

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


    def __repr__(self):
        return f'<{self.__class__.__name__} name={self.name!r} description={self.description!r} type={self.type!r}'


class ApplicationCommand(ApplicationCommandMixin):
    """Represents an application command.

    This class is not user constructible, Use :class:`diskord.application.ApplicationCommand`
    instead.

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

    def __init__(self, data: ApplicationCommandPayload, state: ConnectionState):
        self._state = state
        self._from_data(data)

class ApplicationSlashCommand(ApplicationCommand):
    """Represents a slash application command.

    This class inherits :class:`ApplicationCommand`

    .. note::
        This class is not user constructible, Use :class:`application.SlashCommand` instead.

    Attributes
    ----------
    options: :class:`ApplicationCommandOption`
        The options that belong to this command. (including subcommands or groups.)
    """
    def __init__(self, data: ApplicationCommandPayload, state: ConnectionState):
        self._options: List[ApplicationCommandOption] = (
            ApplicationCommandOption(option, state=state) for option in data.get('options', [])
        )
        super().__init__(data, state)

    def _from_data(self, data: ApplicationCommandPayload) -> ApplicationCommand:
        super()._from_data(data)

        try:
            options = data['options']
            self._options = [ApplicationCommandOption(opt, state=self._state) for opt in options]
        except KeyError:
            pass

        return self

class ApplicationUserCommand(ApplicationCommand):
    """Represents a user application command.

    This class inherits :class:`ApplicationCommand`

    A user command is a context menu command that can be accessed by right clicking
    a user in Discord and selecting the command from "Apps" context menu.

    This class is not user constructible, Use :class:`application.UserCommand` instead.
    """
    def __init__(self, data: ApplicationCommandPayload, state: ConnectionState):
        super().__init__(data, state)

class ApplicationMessageCommand(ApplicationCommand):
    """Represents a message application command.

    This class inherits :class:`ApplicationCommand`

    A message command is a context menu command that can be accessed by right clicking
    a message in Discord and selecting the command from "Apps" context menu.

    This class is not user constructible, Use :class:`application.MessageCommand` instead.
    """
    def __init__(self, data: ApplicationCommandPayload, state: ConnectionState):
        super().__init__(data, state)

class OptionChoice:
    """Represents an option choice for an application command's option.

    This class can be constructed by users.

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

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]):
        return cls(name=dict_["name"], value=dict_["value"])

    def __repr__(self):
        return f"<OptionChoice name={self.name!r} value={self.value!r}>"

    def __str__(self):
        return self.name

class ApplicationCommandOption:
    """Represents an option for an application slash command.

    This class is not user constructible, Use :class:`application.ApplicationCommandOption`
    instead.

    Attributes
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
    choices: List[:class:`OptionChoice`]
        The list of choices this option has.
    channel_types: List[:class:`ChannelType`]
        The channel types that would be shown if :attr:`Option.type` is :attr:`OptionType.channel`
    autocomplete: :class:`bool`
        Whether this option would autocomplete or not.
    max_value: Optional[:class:`int`, :class:`float`]
        The maximum value permitted to be supplied if this option is an integer or number.
        ``None`` if there is no limit.
    min_value: Optional[:class:`int`, :class:`float`]
        The minimum value permitted to be supplied if this option is an integer or number.
        ``None`` if there is no limit.
    """
    if TYPE_CHECKING:
        name: str
        description: str
        type: OptionType
        required: bool
        choices: List[OptionChoice]
        autocomplete: bool
        channel_types: Optional[List[ChannelType]]
        max_value: Optional[Union[int, float]]
        min_value: Optional[Union[int, float]]

    def __init__(self, data: ApplicationCommandOptionPayload, state: ConnectionState):
        self._state = state
        self._update(data)

    def _update(self, data: ApplicationCommandOptionPayload):
        self.name = data['name']
        self.description = data['description']
        self.type = try_enum(OptionType, int(data['type']))
        self.required = data.get('required', filterfalse)
        self.choices = [OptionChoice.from_dict(choice) for choice in data.get('options', [])]
        self.autocomplete = data.get('autocomplete', False)
        self.channel_types = data.get('channel_types')

        if self.channel_types is not None:
            original = self.channel_types
            self.channel_types = []

            for t in original:
                self.channel_types.append(try_enum(ChannelType, int(t)))

        self.max_value = options.get('max_value')
        self.min_value = options.get('min_value')
