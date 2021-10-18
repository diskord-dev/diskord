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
from typing import Optional, Callable, Any, TYPE_CHECKING
from ..enums import ApplicationCommandPermissionType

if TYPE_CHECKING:
    from .command import ApplicationCommand

__all__ = ('ApplicationCommandPermissions', 'CommandPermissionOverwrite', 'permission')

class ApplicationCommandPermissions:
    """A class that allows you to define permissions for an application command
    in a :class:`Guild`.

    Parameters
    -----------
    command: :class:`application.ApplicationCommand`
        The application command whose permissions are being defined.
    guild_id: :class:`int`
        The ID of guild in which permissions are applied.

    Attributes
    ----------
    overwrite: List[:class:`CommandPermissionOverwrite`]
        The overwrites this permissions set holds.
    """
    def __init__(self, guild_id: int, command: ApplicationCommand = None):
        self.command  = command # type: ignore
        self.guild_id = guild_id
        self.overwrites = []

    def get_overwrite(self, entity_id: int) -> Optional[CommandPermissionOverwrite]:
        """Gets permission overwrite for provided entity ID.

        Parameters
        -----------
        entity_id: :class:`int`
            The ID of role or user whose overwrite should be get.

        Returns
        -------
        Optional[:class:`.CommandPermissionOverwrite`]
            The permission overwrite if found, otherwise ``None``
        """
        for overwrite in self.overwrites:
            if overwrite.role_id == entity_id or overwrite.user_id == entity_id:
                return overwrite

    def add_overwrite(self, **options: Any) -> CommandPermissionOverwrite:
        """Adds a permission overwrite to this permissions set.

        Parameters
        -----------
        **options:
            The options of :class:`.CommandPermissionOverwrite`

        Returns
        -------
        :class:`CommandPermissionOverwrite`
            The permission overwrite that was added.
        """
        overwrite = CommandPermissionOverwrite(**options)
        self.overwrites.append(overwrite)
        return overwrite

    def remove_overwrite(self, entity_id: int) -> None:
        """Removes a permission overwrite for provided entity ID.

        This method will not raise error if overwrite is not found.

        Parameters
        -----------
        entity_id: :class:`int`
            The ID of role or user whose overwrite should be removed.
        """
        for overwrite in self.overwrites:
            if overwrite.role_id == entity_id or overwrite.user_id == entity_id:
                return self.overwrites.remove(overwrite)

class CommandPermissionOverwrite:
    """A class that defines an overwrite for :class:`ApplicationCommandPermissions`.

    .. note::
        Either of ``user_id`` or ``role_id`` must be provided.

    Parameters
    -----------
    role_id: :class:`int`
        The ID of role whose overwrite is being defined, this cannot be mixed with ``user_id``
        parameter.
    user_id: :class:`int`
        The ID of user whose overwrite is being defined, this cannot be mixed with ``user_id``
        parameter.
    permission: :class:`bool`
        Whether to allow the command for provided user or role ID. Defaults to ``False``
    """
    if TYPE_CHECKING:
        type: ApplicationCommandType

    def __init__(self, *,
        role_id: Optional[int] = None,
        user_id: Optional[int] = None,
        permission: bool = False,
        ):
        self.role_id = role_id
        self.user_id = user_id
        self.permission = permission

        if self.role_id is not None and self.user_id is not None:
            raise TypeError('role_id and user_id cannot be mixed in permissions')

        if self.role_id is not None:
            self.type = ApplicationCommandPermissionType.role

        elif self.user_id is not None:
            self.type = ApplicationCommandPermissionType.user


    def _get_id(self) -> int:
        if self.type == ApplicationCommandPermissionType.user:
            return self.user_id

        return self.role_id


    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self._get_id(),
            'type': self.type.value,
            'permission': self.permission,
        }


def permission(*, guild_id: int, **options: Any):
    """A decorator that defines the permissions of :class:`application.ApplicationCommand`

    Usage: ::

        @bot.slash_command(guild_ids=[12345], description='Cool command')
        @diskord.application.permission(guild_id=12345, user_id=1234, permission=False)
        @diskord.application.permission(guild_id=12345, role_id=123456, permission=True)
        async def command(ctx):
            await ctx.respond('Hello world')

    In above command, The user with ID ``1234`` would not be able to use to command
    and anyone with role of ID ``123456`` will be able to use the command in the guild
    with ID ``12345``.
    """

    def inner(func: Callable[..., Any]):
        if not hasattr(func, "__application_command_permissions__"):
            func.__application_command_permissions__ = {}

        for original_guild_id in func.__application_command_permissions__:
            if original_guild_id == guild_id:
                perm._permissions[original_guild_id].append(CommandPermissionOverwrite(**options))
                return func

        func.__application_command_permissions__[guild_id] = []
        func.__application_command_permissions__[guild_id].append(CommandPermissionOverwrite(**options))
        return func

    return inner