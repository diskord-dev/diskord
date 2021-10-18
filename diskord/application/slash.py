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
from typing import Union, List, Callable, Any, Optional, TYPE_CHECKING
import inspect

from ..utils import unwrap_function, get_signature_parameters, get
from ..enums import OptionType, ChannelType, ApplicationCommandType
from ..member import Member
from ..user import User
from ..errors import ApplicationCommandError, ApplicationCommandConversionError, ApplicationCommandCheckFailure
from ..interactions import InteractionContext

from .command import ApplicationCommand
from .mixins import ChildrenMixin, OptionsMixin

if TYPE_CHECKING:
    from ..application_commands import OptionChoice
    from ..interactions import Interaction
    from ..types.interactions import (
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
    )

__all__ = (
    'Option',
    'SlashCommand',
    'SlashCommandChild',
    'SlashCommandGroup',
    'SlashSubCommand',
    'option',
    'slash_command'
)



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
            @diskord.option('item', autocomplete=autocomplete)
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
        converter: "Converter" = None, # type: ignore
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
        return get(self._choices, **attrs)

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
        from ..application_commands import OptionChoice

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
        choice = get(self._choices, **attrs)
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
        return get(self._options, **attrs)

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
        option = get(self._options, **attrs)
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
        return bool(self.autocomplete)

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
        self._type: ApplicationCommandType = ApplicationCommandType.slash
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
                # self._client will not be None
                value = self._client.get_user(int(option["value"]))

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
                        state=self._state,
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

    async def resolve_autocomplete_choices(self, interaction):
        """|coro|

        Resolves autocompletion choices for command.

        This should rarely be called as it is automatically handled
        by the library under-the-hood.

        Parameters
        -----------
        interaction: :class:`Interaction`
            The autocomplete interaction.
        """
        data = interaction.data
        options = data['options']

        for option in options:
            if option['type'] == OptionType.sub_command.value:
                command = self.get_child(name=option['name'])

                for sub in option['options']:
                    if 'focused' in sub:
                        option = sub
                        break

            elif option['type'] == OptionType.sub_command_group.value:
                if self.type == OptionType.sub_command:
                    command = self
                else:
                    group = self.get_child(name=option['name'])
                    command = group.get_child(name=option['options'][0]['name'])

                for sub in option['options'][0]['options']:
                    if 'focused' in sub:
                        option = sub
                        break

        resolved_option = self.get_option(name=option['name'])

        if self.cog is not None:
            choices = await resolved_option.autocomplete(self.cog, option['value'], interaction)
        else:
            choices = await resolved_option.autocomplete(option['value'], interaction)

        if not isinstance(choices, list):
            raise TypeError(f'autocomplete for {resolved_option.name} returned {choices.__class__.__name__}, Expected list.')

        return choices


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

        self._client.dispatch('application_command', context)
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
        @diskord.option('role', description='The role to clear permissions of.')
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


def option(name: str, **attrs) -> Option:
    """A decorator-based interface to add options to a slash command.

    Usage: ::

        @bot.slash_command(description="Highfive a member!")
        @diskord.option('member', description='The member to high-five.')
        @diskord.option('reason', description='Reason to high-five')

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

        @diskord.application.slash_command(description='My cool slash command.')
        async def test(ctx):
            await ctx.respond('Hello world')
    """

    def inner(func: Callable):
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Callback function must be a coroutine.")

        return SlashCommand(func, **options)

    return inner
