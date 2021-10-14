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


class ApplicationCommand:
    """Represents an application command.

    This class is not user constructible, Use :class:`diskord.application.ApplicationCommand`
    instead for that purpose.

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


### --- Application Commands End --- ###


### --- Context Menu Commands Start --- ###

### --- Context Menu Commands End --- ###


### --- Slash Commands Start --- ###

### --- Slash Commands End --- ###


### --- Decorators Start --- ###
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
