# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2021-present NerdGuyAhmad

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
from typing import Callable, Any, Dict, List, Optional, TYPE_CHECKING
import asyncio
import logging
import traceback

from ..utils import get as utils_get
from ..application_commands import ApplicationCommandMixin
from ..errors import ApplicationCommandError, _BaseCommandError, Forbidden
from ..enums import OptionType, ApplicationCommandType, try_enum
from .mixins import ChecksMixin
from .types import Check
from .permissions import ApplicationCommandPermissions

if TYPE_CHECKING:
    from .slash import SlashCommand
    from ..types.interactions import ApplicationCommand as ApplicationCommandPayload
    from ..state import ConnectionState
    from ..interactions import Interaction, InteractionContext

_log = logging.getLogger(__name__)

class ApplicationCommand(ApplicationCommandMixin, ChecksMixin):
    """Represents an application command.

    This is base class for all user constructible application commands classes like
    :class:`SlashCommand` etc.

    This class also inherits :class:`diskord.ApplicationCommand`

    Parameters
    ----------
    callback:
        The callback function of this command.
    name: :class:`str`
        The name of application command. By default, callback's name is used.
    description: :class:`str`
        The description of application command. Defaults to the docstring of callback
        or ``No description.``
    guild_ids: List[:class:`int`]
        The list of guild IDs to register command in, if not global.
    default_permission: :class:`bool`
        The default permission of the application command. Setting this to ``False``
        disables the command for everyone unless certain permission overwrite is configured.
    extras: :class:`dict`
        A dict of user provided extras to attach to the Command. Use this to attach some
        extra info to command that you might need later.
    id: :class:`int`
        The ID of the command, If this is provided, this command will not be registered
        by library. Instead, it will be added to application commands cache directly and
        interactions will be handled directly. As such, there will be no need to call
        :meth:`~diskord.Client.register_application_commands` in :func:`~diskord.on_connect`
        to register this command manually.

        This allows you to register application commands in a separate (independent) way without
        worrying about commands registration problems like accidentally overwriting commands.

        The ID must be integer and valid *registered* application command ID.

    Attributes
    ----------
    checks: List[Callable[:class:`InteractionContext`, bool]]
        The list of checks this commands holds that will be checked before command's
        invocation.

        For more info on checks and how to register them, See :func:`~ext.commands.check`
        documentation as these checks actually come from there.
    """
    _type: ApplicationCommandType

    def __init__(self, callback: Callable, **attrs: Any):
        self._callback = callback
        self._guild_ids = attrs.pop("guild_ids", None)
        self._description = (
            attrs.pop("description", callback.__doc__) or "No description"
        )
        self._name = attrs.pop("name", callback.__name__)
        self._default_permission = attrs.pop("default_permission", True)
        self.extras: Dict[str, Any] = attrs.pop("extras", {})

        self._cog = None
        self._state = None # type: ignore

        self._id: Optional[int]
        try:
            self._id = int(attrs['id'])
        except KeyError:
            self._id = None

        self._application_id: Optional[int] = None
        self._guild_id: Optional[int] = None
        self._version: Optional[int] = None
        self._update_callback_data()

    def is_global_command(self) -> bool:
        """:class:`bool`: Whether the command is global command or not."""
        return (not self._guild_ids)

    def _update_callback_data(self):
        self.permissions: List[ApplicationCommandPermissions] = []
        try:
            permissions = self.callback.__application_command_permissions__
        except AttributeError:
            permissions = {}  # type: ignore

        for guild in permissions:
            perms = ApplicationCommandPermissions(command=self, guild_id=guild)
            perms.overwrites = permissions[guild]

            self.permissions.append(perms)

        self.checks: List[Check]
        try:
            self.checks = self.callback.__commands_checks__
            self.checks.reverse()
        except AttributeError:
            self.checks = []

    @property
    def _client(self):
        return self._state._get_client()

    _bot = _client

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
            self.append_option(opt) # type: ignore

        self._update_callback_data()

    @property
    def guild_ids(self) -> Optional[List[int]]:
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

    async def invoke(self, context: InteractionContext):
        raise NotImplementedError

    async def _edit_permissions(self, permissions: ApplicationCommandPermissions):
        data = await super()._edit_permissions(permissions)

        new = self.add_permissions(guild_id=int(data['guild_id']))
        new.overwrites = permissions.overwrites


    # permissions management

    def add_permissions(self, guild_id: int) -> ApplicationCommandPermissions:
        """Adds a :class:`~application.ApplicationCommandPermissions` to the command.

        If this method is called after the commands were synced or clean registered
        initially, you might need to recall :meth:`Client.sync_application_commands`
        in order for changes to take affect.

        This method would overwrite existing permissions set for this guild if any.

        Parameters
        ----------
        guild_id: :class:`int`
            The ID of guild to add permissions for.

        Returns
        -------
        :class:`~application.ApplicationCommandPermissions`
            The permissions that were added.
        """
        original = self.get_permissions(guild_id)
        if original:
            self.remove_permissions(guild_id)

        permission = ApplicationCommandPermissions(command=self, guild_id=guild_id)
        self.permissions.append(permission)
        return permission

    def remove_permissions(self, guild_id: int) -> None:
        """Removes a :class:`~application.ApplicationCommandPermissions` from the command.

        If this method is called after the commands were synced or clean registered
        initially, you might need to recall :meth:`Client.sync_application_commands`
        in order for changes to take affect.

        This function does not raise an error if the permissions set for the guild
        is not found.

        Parameters
        ----------
        guild_id: :class:`int`
            The ID of guild whose permissions are being removed.
        """
        permission = utils_get(self.permissions, guild_id=guild_id)
        if not permission:
            return

        self.permissions.remove(permission)

    def get_permissions(self, guild_id: int) -> Optional[ApplicationCommandPermissions]:
        """Gets a :class:`~application.ApplicationCommandPermissions` from the command
        for the provided guild ID.

        This function does not raise an error if the permissions set for the guild
        is not found, instead, it returns ``None``

        Parameters
        ----------
        guild_id: :class:`int`
            The ID of guild whose permissions are required.
        """
        return utils_get(self.permissions, guild_id=guild_id)

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name!r} description={self.description!r} guild_id={self.guild_id!r} id={self.id!r}"

    def __str__(self):
        return self.name

class ApplicationCommandStore:
    def __init__(self, state: ConnectionState):
        self._pending: List[ApplicationCommand] = []
        self._commands: Dict[int, ApplicationCommand] = {}
        self._state = state

    def get_application_command(self, command_id: int):
        try:
            return self._commands[command_id] # type: ignore
        except KeyError:
            return

    def add_application_command(self, command: ApplicationCommand):
        self._commands[command.id] = command # type: ignore

    def remove_application_command(self, id: int):
        return self._commands.pop(id, None) # type: ignore

    def add_pending_command(self, command: ApplicationCommand):
        if not isinstance(command, ApplicationCommand):
            raise TypeError(
                "command parameter must be an instance of application.ApplicationCommand."
            )

        command._state = self._state

        if not hasattr(command.callback, "__application_command_params__"):
            command.callback.__application_command_params__ = {}

        for opt in command.callback.__application_command_params__.values():
            command.append_option(opt) # type: ignore

        if command.id is not None:
            self.add_application_command(command)
        else:
            self._pending.append(command)

        # reset the params so they don't conflict if user decides to re-add this
        # command.
        command.callback.__application_command_params__ = {}
        return command

    def remove_pending_command(self, command: ApplicationCommand):
        try:
            self._pending.remove(command)
        except ValueError:
            return

    async def _dispatch_command(self, command: ApplicationCommand, interaction: Interaction):
        # _get_client will never be unavailable at this point
        client = self._state._get_client() # type: ignore
        context = client.get_interaction_context(interaction)

        try:
            await command.invoke(context)
        except (ApplicationCommandError, _BaseCommandError) as error:
            self._state.dispatch("application_command_error", context, error)
        else:
            self._state.dispatch("application_command_completion", context)

    def dispatch(self, interaction: Interaction):
        try:
            command_id = int(interaction.data['id']) # type: ignore
        except (KeyError, ValueError):
            return

        command = self.get_application_command(command_id)

        if command is None:
            return self._state.dispatch('unknown_application_command', interaction)

        asyncio.create_task(
            self._dispatch_command(command, interaction),
            name=f"discord-application-command-dispatch-{command.id}",
        )

    async def _dispatch_autocomplete(self, interaction):
        command: SlashCommand = self.get_application_command(int(interaction.data['id'])) # type: ignore

        if not command:
            return

        for option in interaction.data['options']:
            if option['type'] == OptionType.sub_command.value:
                command = command.get_child(name=option['name']) # type: ignore
            elif option['type'] == OptionType.sub_command_group.value:
                grp = command.get_child(name=option['name'])
                # first element is the command being used.
                command = grp.get_child(name=option['options'][0]['name']) # type: ignore

        choices = await command.resolve_autocomplete_choices(interaction)
        await interaction.response.autocomplete(choices)


    def dispatch_autocomplete(self, interaction: Interaction):
        asyncio.create_task(
            self._dispatch_autocomplete(interaction),
            name=f"discord-application-command-autocomplete-dispatch-{interaction.data['id']}", # type: ignore
        )

    async def sync_application_commands(self, *, delete_unregistered_commands: bool = True):

        _log.info("Synchronizing internal cache commands.")

        if not self._pending:
            # since we don't have any commands pending to register then
            # we just return
            return

        client = self._state._get_client()
        commands = await self._state.http.get_global_commands(client.user.id)
        non_registered = []

        # Synchronising the fetched commands with internal cache.
        for command in commands:
            # trying to find the command in the pending commands
            # that matches the fetched command traits.
            registered = utils_get(
                [c for c in self._pending if not c.guild_ids],
                name=command["name"],
                type=try_enum(ApplicationCommandType, int(command["type"])), # type: ignore
            )
            if registered is None:
                # the command not found, so append it to list of uncached
                # commands.
                non_registered.append(command)
                continue

            # command found, sync it and add it.
            self.add_application_command(registered._from_data(command))
            self.remove_pending_command(registered)


        # Deleting the command that weren't created.
        if delete_unregistered_commands:
            for command in non_registered:
                if command.get("guild_id"):
                    await self._state.http.delete_guild_command(
                        client.user.id, command["guild_id"], command["id"]
                    )
                else:
                    await self._state.http.delete_global_command(client.user.id, command["id"])

        # Registering the remaining commands

        guilds = {}

        # registering the guild commands. they don't take an hour to update
        # so we don't mind bulk upserting them.
        for command in self._pending:
            if not command.guild_ids:
                continue

            for guild in set(command.guild_ids):
                if not guild in guilds:
                    guilds[guild] = []

                guilds[guild].append(command.to_dict())

        for guild in guilds:
            try:
                cmds = await self._state.http.bulk_upsert_guild_commands(
                    client.user.id, guild, guilds[guild]
                )
            except Forbidden as e:
                # the bot is missing application.commands scope so cannot
                # make the command in the guild
                traceback.print_exc()
                continue
            else:
                for cmd in cmds:
                    command = utils_get(
                        self._pending,
                        name=cmd["name"],
                        type=try_enum(ApplicationCommandType, int(cmd["type"])), # type: ignore
                    )
                    self.add_application_command(command._from_data(cmd))
                    self.remove_pending_command(command) # type: ignore

        # now time for rest of global commands that are
        # new. at this point, self._pending should only have *new* *global*
        # commands.
        while self._pending:
            index = len(self._pending) - 1
            command = self._pending[index]
            data = await self._state.http.upsert_global_command(client.user.id, command.to_dict())
            self.add_application_command(command._from_data(data))
            self._pending.pop(index)

    async def clean_register(self):
        # This needs a refactor as current implementation is kind of hacky and can
        # be unstable.

        if not self._pending:
            # since we don't have any commands pending, we will do nothing and return
            return

        client = self._state._get_client()
        _log.info(
            "Clean Registering %s application commands."
            % str(len(self._pending))
        )

        commands = []

        # Firstly, We will register the global commands
        for command in (cmd for cmd in self._pending if not cmd.guild_ids):
            data = command.to_dict()
            commands.append(data)

        cmds = await self._state.http.bulk_upsert_global_commands(client.user.id, commands)

        for cmd in cmds:
            command = utils_get(
                self._pending,
                name=cmd["name"],
                type=try_enum(ApplicationCommandType, int(cmd["type"])), # type: ignore
            )
            self.add_application_command(command._from_data(cmd))
            self.remove_pending_command(command) # type: ignore

        # Registering the guild commands now

        guilds = {}

        for cmd in (command for command in self._pending if command.guild_ids):
            data = cmd.to_dict()
            for guild in cmd.guild_ids:
                if guilds.get(guild) is None:
                    guilds[guild] = []

                guilds[guild].append(data)

        for guild in guilds:
            try:
                cmds = await self._state.http.bulk_upsert_guild_commands(
                    client.user.id, guild, guilds[guild]
                )
            except Forbidden as e:
                # bot doesn't has application.commands scope
                traceback.print_exc()
                continue
            else:
                for cmd in cmds:
                    command = utils_get(
                        self._pending,
                        name=cmd["name"],
                        type=try_enum(ApplicationCommandType, int(cmd["type"])), # type: ignore
                    )
                    self.add_application_command(command._from_data(cmd))
                    self.remove_pending_command(command) # type: ignore