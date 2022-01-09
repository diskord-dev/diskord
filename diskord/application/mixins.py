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
from typing import (
    Any,
    List,
    Optional,
    TYPE_CHECKING,
    Callable,
)
from ..utils import async_all, maybe_coroutine, get
from .types import Check
from ..errors import ApplicationCommandCheckFailure

if TYPE_CHECKING:
    from ..interactions import InteractionContext
    from .slash import SlashCommandChild, Option


class ChildrenMixin:
    """A mixin that implements children for slash commands or slash subcommand groups."""
    _children: List[SlashCommandChild]
    _options: List[Option]

    @property
    def children(self) -> List[SlashCommandChild]:
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
        return get(self._children, **attrs)

    def add_child(self, child: SlashCommandChild) -> SlashCommandChild:
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
        child._parent = self # type: ignore
        self._children.append(child)

        if not hasattr(child.callback, "__application_command_params__"):
            child.callback.__application_command_params__ = {}

        for opt in child.callback.__application_command_params__.values():
            child.append_option(opt)

        # resetting the params so if user tries to re-add the command, the params
        # don't get duplicated.
        child.callback.__application_command_params__ = {}

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
        child = get(self._children, **attrs)
        if child:
            self._children.remove(child)

        return child


class OptionsMixin:
    """A mixin that implements basic slash commands and subcommands options."""
    _options: List[Option]

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
        return get(self._options, **attrs)

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
        option._parent = self # type: ignore
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
        option._parent = self # type: ignore
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
        option = get(self._options, **attrs)
        if option:
            self._options.remove(option)

        return option


class ChecksMixin:
    """A mixin that implements checks for application commands."""
    checks: List[Check]

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
            if not await ctx.bot.can_run(ctx): # type: ignore
                raise ApplicationCommandCheckFailure(
                    f"The global check functions for command {self.name} failed." # type: ignore
                )

        cog = self.cog # type: ignore
        if cog is not None:
            local_check = type(cog)._get_overridden_method(cog.cog_check)
            if local_check is not None:
                ret = await maybe_coroutine(local_check, ctx)
                if not ret:
                    return False

        predicates = self.checks
        if not predicates:
            # since we have no checks, then we just return True.
            return True

        return await async_all(predicate(ctx) for predicate in predicates)  # type: ignore
