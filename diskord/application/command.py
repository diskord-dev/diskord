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
from typing import Callable, Any, Dict, List
import asyncio

from ..application_commands import ApplicationCommandMixin
from ..errors import ApplicationCommandError, _BaseCommandError
from ..enums import OptionType
from .mixins import ChecksMixin
from .types import Check

# TODO: permissions fix.

class ApplicationCommand(ApplicationCommandMixin, ChecksMixin):
    """Represents an application command.

    This is base class for all user constructible application commands classes like
    :class:`SlashCommand` etc.

    This class also inherits :class:`diskord.ApplicationCommand`

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
        self._client = None

        self._from_data(dict())
        self._update_callback_data()

    def is_global_command(self) -> bool:
        """:class:`bool`: Whether the command is global command or not."""
        return len(self._guild_ids) == 0

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

        self._permissions: List[GuildApplicationCommandPermissions] = permissions

    @property
    def _bot(self):
        # a simple alias to not break ext.commands
        return self._client

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
    def permissions(self) -> List[GuildApplicationCommandPermissions]:
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

    async def invoke(self):
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name!r} description={self.description!r} guild_id={self.guild_id!r} id={self.id!r}"

    def __str__(self):
        return self.name

class ApplicationCommandStore:
    def __init__(self, state: ConnectionState):
        self._commands: Dict[int, ApplicationCommand] = {}
        self._state = state

    def get_application_command(self, command_id: int):
        try:
            return self._commands[command_id] # type: ignore
        except KeyError:
            return

    def add_application_command(self, command: ApplicationCommand):
        self._commands[command.id] = command

    def remove_application_command(self, id: int):
        return self._commands.pop(id, None) # type: ignore

    async def _dispatch_command(self, command: ApplicationCommand, interaction: Interaction):
        # _get_client will never be unavailable at this point
        client = self._state._get_client() # type: ignore
        context = client.get_application_context(interaction)

        try:
            await command.invoke(context)
        except (ApplicationCommandError, _BaseCommandError) as error:
            self._state.dispatch("application_command_error", context, error)
        else:
            self._state.dispatch("application_command_completion", context)

    def dispatch(self, interaction: Interaction):
        try:
            command_id = int(interaction.data['id'])
        except KeyError:
            return

        command = self.get_application_command(command_id)

        if command is None:
            return self._state.dispatch('unknown_application_command', interaction)

        asyncio.create_task(
            self._dispatch_command(command, interaction),
            name=f"discord-application-command-dispatch-{command.id}",
        )

    async def _dispatch_autocomplete(self, command, interaction):
        data = interaction.data
        options = data['options']

        for option in options:
            if option['type'] == OptionType.sub_command.value:
                command = command.get_child(name=option['name'])

                for sub in option['options']:
                    if 'focused' in sub:
                        option = sub
                        break

            elif option['type'] == OptionType.sub_command_group.value:
                group = command.get_child(name=option['name'])
                command = group.get_child(name=option['options'][0]['name'])

                for sub in option['options'][0]['options']:
                    if 'focused' in sub:
                        option = sub
                        break

        resolved_option = command.get_option(name=option['name'])

        if command.cog is not None:
            choices = await resolved_option.autocomplete(command.cog, option['value'], interaction)
        else:
            choices = await resolved_option.autocomplete(option['value'], interaction)

        if not isinstance(choices, list):
            raise TypeError(f'autocomplete for {resolved_option.name} returned {choices.__class__.__name__}, Expected list.')

        await interaction.response.autocomplete(choices)


    def dispatch_autocomplete(self, interaction: Interaction):
        command = self.get_application_command(int(interaction.data['id']))

        if command is None:
            return self._state.dispatch('unknown_application_command', interaction)

        asyncio.create_task(
            self._dispatch_autocomplete(command, interaction),
            name=f"discord-application-command-autocomplete-dispatch-{command.id}",
        )

