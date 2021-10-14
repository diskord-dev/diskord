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
from typing import Callable, Any, TYPE_CHECKING
import inspect

from ..enums import ApplicationCommandType
from ..member import Member
from ..user import User
from ..message import Message

from .command import ApplicationCommand

if TYPE_CHECKING:
    from ..interactions import InteractionContext
    from ..interactions import Interaction

__all__ = (
    'UserCommand',
    'MessageCommand',
    'user_command',
    'message_command'
)

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

        self._client.dispatch('application_command', context)
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

        self._client.dispatch('application_command', context)
        await context.command.callback(*args)




def user_command(**options) -> Callable[..., Any]:
    """A decorator that converts a function to :class:`UserCommand`

    Usage: ::

        @diskord.application.user_command()
        async def test(ctx, user):
            await ctx.respond('Hello world')
    """

    def inner(func: Callable[..., Any]) -> UserCommand:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Callback function must be a coroutine.")
        options["name"] = options.get("name") or func.__name__

        return UserCommand(func, **options)

    return inner


def message_command(**options) -> Callable[..., Any]:
    """A decorator that converts a function to :class:`MessageCommand`

    Usage: ::

        @diskord.application.message_command()
        async def test(ctx, message):
            await ctx.respond('Hello world')

    Parameters
    ----------
    **options:
        The options of :class:`MessageCommand`
    """

    def inner(func: Callable[..., Any]) -> MessageCommand:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Callback function must be a coroutine.")
        options["name"] = options.get("name") or func.__name__

        return MessageCommand(func, **options)

    return inner


