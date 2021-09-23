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
)
import asyncio

from . import utils
from . import abc
from .enums import (
    try_enum,
    ApplicationCommandType,
    OptionType,
    InteractionType,
    InteractionResponseType,
    ApplicationCommandPermissionType,
)
from .errors import InteractionResponded, HTTPException, ClientException
from .channel import PartialMessageable, ChannelType

from .user import User
from .member import Member
from .message import Message, Attachment
from .object import Object
from .permissions import Permissions
from .webhook.async_ import async_context, Webhook, handle_message_parameters

__all__ = (
    'Interaction',
    'InteractionMessage',
    'InteractionResponse',
    'ApplicationCommand',
    'SlashCommand',
    'SlashSubCommand',
    'UserCommand',
    'MessageCommand',
    'Option',
    'OptionChoice',
)

if TYPE_CHECKING:
    from .types.interactions import (
        Interaction as InteractionPayload,
        InteractionData,
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
        ApplicationCommandPermissions as ApplicationCommandPermissionsPayload,
    )
    from .guild import Guild
    from .state import ConnectionState
    from .file import File
    from .mentions import AllowedMentions
    from aiohttp import ClientSession
    from .embeds import Embed
    from .ui.view import View
    from .channel import VoiceChannel, StageChannel, TextChannel, CategoryChannel, StoreChannel, PartialMessageable
    from .threads import Thread
    from .bot import Bot

    InteractionChannel = Union[
        VoiceChannel, StageChannel, TextChannel, CategoryChannel, StoreChannel, Thread, PartialMessageable
    ]

MISSING: Any = utils.MISSING


class Interaction:
    """Represents a Discord interaction.

    An interaction happens when a user does an action that needs to
    be notified. Current examples are slash commands and components.

    .. versionadded:: 2.0

    Attributes
    -----------
    id: :class:`int`
        The interaction's ID.
    type: :class:`InteractionType`
        The interaction type.
    guild_id: Optional[:class:`int`]
        The guild ID the interaction was sent from.
    channel_id: Optional[:class:`int`]
        The channel ID the interaction was sent from.
    application_id: :class:`int`
        The application ID that the interaction was for.
    user: Optional[Union[:class:`User`, :class:`Member`]]
        The user or member that sent the interaction.
    message: Optional[:class:`Message`]
        The message that sent this interaction.
    token: :class:`str`
        The token to continue the interaction. These are valid
        for 15 minutes.
    data: :class:`dict`
        The raw interaction data.
    """

    __slots__: Tuple[str, ...] = (
        'id',
        'type',
        'guild_id',
        'channel_id',
        'data',
        'application_id',
        'message',
        'user',
        'token',
        'version',
        '_permissions',
        '_state',
        '_session',
        '_original_message',
        '_cs_response',
        '_cs_followup',
        '_cs_channel',
    )

    def __init__(self, *, data: InteractionPayload, state: ConnectionState):
        self._state: ConnectionState = state
        self._session: ClientSession = state.http._HTTPClient__session
        self._original_message: Optional[InteractionMessage] = None
        self._from_data(data)

    def _from_data(self, data: InteractionPayload):
        self.id: int = int(data['id'])
        self.type: InteractionType = try_enum(InteractionType, data['type'])
        self.data: Optional[InteractionData] = data.get('data')
        self.token: str = data['token']
        self.version: int = data['version']
        self.channel_id: Optional[int] = utils._get_as_snowflake(data, 'channel_id')
        self.guild_id: Optional[int] = utils._get_as_snowflake(data, 'guild_id')
        self.application_id: int = int(data['application_id'])

        self.message: Optional[Message]
        try:
            self.message = Message(state=self._state, channel=self.channel, data=data['message'])  # type: ignore
        except KeyError:
            self.message = None

        self.user: Optional[Union[User, Member]] = None
        self._permissions: int = 0

        # TODO: there's a potential data loss here
        if self.guild_id:
            guild = self.guild or Object(id=self.guild_id)
            try:
                member = data['member']  # type: ignore
            except KeyError:
                pass
            else:
                self.user = Member(state=self._state, guild=guild, data=member)  # type: ignore
                self._permissions = int(member.get('permissions', 0))
        else:
            try:
                self.user = User(state=self._state, data=data['user'])
            except KeyError:
                pass

    def is_application_command(self):
        """:class:`bool`: Whether the interaction is an application command or not."""

        return self.type == InteractionType.application_command

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild the interaction was sent from."""
        return self._state and self._state._get_guild(self.guild_id)

    @utils.cached_slot_property('_cs_channel')
    def channel(self) -> Optional[InteractionChannel]:
        """Optional[Union[:class:`abc.GuildChannel`, :class:`PartialMessageable`, :class:`Thread`]]: The channel the interaction was sent from.

        Note that due to a Discord limitation, DM channels are not resolved since there is
        no data to complete them. These are :class:`PartialMessageable` instead.
        """
        guild = self.guild
        channel = guild and guild._resolve_channel(self.channel_id)
        if channel is None:
            if self.channel_id is not None:
                type = ChannelType.text if self.guild_id is not None else ChannelType.private
                return PartialMessageable(state=self._state, id=self.channel_id, type=type)
            return None
        return channel

    @property
    def permissions(self) -> Permissions:
        """:class:`Permissions`: The resolved permissions of the member in the channel, including overwrites.

        In a non-guild context where this doesn't apply, an empty permissions object is returned.
        """
        return Permissions(self._permissions)

    @utils.cached_slot_property('_cs_response')
    def response(self) -> InteractionResponse:
        """:class:`InteractionResponse`: Returns an object responsible for handling responding to the interaction.

        A response can only be done once. If secondary messages need to be sent, consider using :attr:`followup`
        instead.
        """
        return InteractionResponse(self)

    @utils.cached_slot_property('_cs_followup')
    def followup(self) -> Webhook:
        """:class:`Webhook`: Returns the follow up webhook for follow up interactions."""
        payload = {
            'id': self.application_id,
            'type': 3,
            'token': self.token,
        }
        return Webhook.from_state(data=payload, state=self._state)

    async def original_message(self) -> InteractionMessage:
        """|coro|

        Fetches the original interaction response message associated with the interaction.

        If the interaction response was :meth:`InteractionResponse.send_message` then this would
        return the message that was sent using that response. Otherwise, this would return
        the message that triggered the interaction.

        Repeated calls to this will return a cached value.

        Raises
        -------
        HTTPException
            Fetching the original response message failed.
        ClientException
            The channel for the message could not be resolved.

        Returns
        --------
        InteractionMessage
            The original interaction response message.
        """

        if self._original_message is not None:
            return self._original_message

        # TODO: fix later to not raise?
        channel = self.channel
        if channel is None:
            raise ClientException('Channel for message could not be resolved')

        adapter = async_context.get()
        data = await adapter.get_original_interaction_response(
            application_id=self.application_id,
            token=self.token,
            session=self._session,
        )
        state = _InteractionMessageState(self, self._state)
        message = InteractionMessage(state=state, channel=channel, data=data)  # type: ignore
        self._original_message = message
        return message

    async def edit_original_message(
        self,
        *,
        content: Optional[str] = MISSING,
        embeds: List[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        file: File = MISSING,
        files: List[File] = MISSING,
        view: Optional[View] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
    ) -> InteractionMessage:
        """|coro|

        Edits the original interaction response message.

        This is a lower level interface to :meth:`InteractionMessage.edit` in case
        you do not want to fetch the message and save an HTTP request.

        This method is also the only way to edit the original message if
        the message sent was ephemeral.

        Parameters
        ------------
        content: Optional[:class:`str`]
            The content to edit the message with or ``None`` to clear it.
        embeds: List[:class:`Embed`]
            A list of embeds to edit the message with.
        embed: Optional[:class:`Embed`]
            The embed to edit the message with. ``None`` suppresses the embeds.
            This should not be mixed with the ``embeds`` parameter.
        file: :class:`File`
            The file to upload. This cannot be mixed with ``files`` parameter.
        files: List[:class:`File`]
            A list of files to send with the content. This cannot be mixed with the
            ``file`` parameter.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this message.
            See :meth:`.abc.Messageable.send` for more information.
        view: Optional[:class:`~discord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.

        Raises
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Edited a message that is not yours.
        TypeError
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``
        ValueError
            The length of ``embeds`` was invalid.

        Returns
        --------
        :class:`InteractionMessage`
            The newly edited message.
        """

        previous_mentions: Optional[AllowedMentions] = self._state.allowed_mentions
        params = handle_message_parameters(
            content=content,
            file=file,
            files=files,
            embed=embed,
            embeds=embeds,
            view=view,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_mentions,
        )
        adapter = async_context.get()
        data = await adapter.edit_original_interaction_response(
            self.application_id,
            self.token,
            session=self._session,
            payload=params.payload,
            multipart=params.multipart,
            files=params.files,
        )

        # The message channel types should always match
        message = InteractionMessage(state=self._state, channel=self.channel, data=data)  # type: ignore
        if view and not view.is_finished():
            self._state.store_view(view, message.id)
        return message

    async def delete_original_message(self) -> None:
        """|coro|

        Deletes the original interaction response message.

        This is a lower level interface to :meth:`InteractionMessage.delete` in case
        you do not want to fetch the message and save an HTTP request.

        Raises
        -------
        HTTPException
            Deleting the message failed.
        Forbidden
            Deleted a message that is not yours.
        """
        adapter = async_context.get()
        await adapter.delete_original_interaction_response(
            self.application_id,
            self.token,
            session=self._session,
        )


class InteractionResponse:
    """Represents a Discord interaction response.

    This type can be accessed through :attr:`Interaction.response`.

    .. versionadded:: 2.0
    """

    __slots__: Tuple[str, ...] = (
        '_responded',
        '_parent',
    )

    def __init__(self, parent: Interaction):
        self._parent: Interaction = parent
        self._responded: bool = False

    def is_done(self) -> bool:
        """:class:`bool`: Indicates whether an interaction response has been done before.

        An interaction can only be responded to once.
        """
        return self._responded

    async def defer(self, *, ephemeral: bool = False) -> None:
        """|coro|

        Defers the interaction response.

        This is typically used when the interaction is acknowledged
        and a secondary action will be done later.

        Parameters
        -----------
        ephemeral: :class:`bool`
            Indicates whether the deferred message will eventually be ephemeral.
            This only applies for interactions of type :attr:`InteractionType.application_command`.

        Raises
        -------
        HTTPException
            Deferring the interaction failed.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        defer_type: int = 0
        data: Optional[Dict[str, Any]] = None
        parent = self._parent
        if parent.type is InteractionType.component:
            defer_type = InteractionResponseType.deferred_message_update.value
        elif parent.type is InteractionType.application_command:
            defer_type = InteractionResponseType.deferred_channel_message.value
            if ephemeral:
                data = {'flags': 64}

        if defer_type:
            adapter = async_context.get()
            await adapter.create_interaction_response(
                parent.id, parent.token, session=parent._session, type=defer_type, data=data
            )
            self._responded = True

    async def pong(self) -> None:
        """|coro|

        Pongs the ping interaction.

        This should rarely be used.

        Raises
        -------
        HTTPException
            Ponging the interaction failed.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent
        if parent.type is InteractionType.ping:
            adapter = async_context.get()
            await adapter.create_interaction_response(
                parent.id, parent.token, session=parent._session, type=InteractionResponseType.pong.value
            )
            self._responded = True

    async def send_message(
        self,
        content: Optional[Any] = None,
        *,
        embed: Embed = MISSING,
        embeds: List[Embed] = MISSING,
        view: View = MISSING,
        tts: bool = False,
        ephemeral: bool = False,
    ) -> None:
        """|coro|

        Responds to this interaction by sending a message.

        Parameters
        -----------
        content: Optional[:class:`str`]
            The content of the message to send.
        embeds: List[:class:`Embed`]
            A list of embeds to send with the content. Maximum of 10. This cannot
            be mixed with the ``embed`` parameter.
        embed: :class:`Embed`
            The rich embed for the content to send. This cannot be mixed with
            ``embeds`` parameter.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        view: :class:`discord.ui.View`
            The view to send with the message.
        ephemeral: :class:`bool`
            Indicates if the message should only be visible to the user who started the interaction.
            If a view is sent with an ephemeral message and it has no timeout set then the timeout
            is set to 15 minutes.

        Raises
        -------
        HTTPException
            Sending the message failed.
        TypeError
            You specified both ``embed`` and ``embeds``.
        ValueError
            The length of ``embeds`` was invalid.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        payload: Dict[str, Any] = {
            'tts': tts,
        }

        if embed is not MISSING and embeds is not MISSING:
            raise TypeError('cannot mix embed and embeds keyword arguments')

        if embed is not MISSING:
            embeds = [embed]

        if embeds:
            if len(embeds) > 10:
                raise ValueError('embeds cannot exceed maximum of 10 elements')
            payload['embeds'] = [e.to_dict() for e in embeds]

        if content is not None:
            payload['content'] = str(content)

        if ephemeral:
            payload['flags'] = 64

        if view is not MISSING:
            payload['components'] = view.to_components()

        parent = self._parent
        adapter = async_context.get()
        await adapter.create_interaction_response(
            parent.id,
            parent.token,
            session=parent._session,
            type=InteractionResponseType.channel_message.value,
            data=payload,
        )

        if view is not MISSING:
            if ephemeral and view.timeout is None:
                view.timeout = 15 * 60.0

            self._parent._state.store_view(view)

        self._responded = True

    async def edit_message(
        self,
        *,
        content: Optional[Any] = MISSING,
        embed: Optional[Embed] = MISSING,
        embeds: List[Embed] = MISSING,
        attachments: List[Attachment] = MISSING,
        view: Optional[View] = MISSING,
    ) -> None:
        """|coro|

        Responds to this interaction by editing the original message of
        a component interaction.

        Parameters
        -----------
        content: Optional[:class:`str`]
            The new content to replace the message with. ``None`` removes the content.
        embeds: List[:class:`Embed`]
            A list of embeds to edit the message with.
        embed: Optional[:class:`Embed`]
            The embed to edit the message with. ``None`` suppresses the embeds.
            This should not be mixed with the ``embeds`` parameter.
        attachments: List[:class:`Attachment`]
            A list of attachments to keep in the message. If ``[]`` is passed
            then all attachments are removed.
        view: Optional[:class:`~discord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.

        Raises
        -------
        HTTPException
            Editing the message failed.
        TypeError
            You specified both ``embed`` and ``embeds``.
        InteractionResponded
            This interaction has already been responded to before.
        """
        if self._responded:
            raise InteractionResponded(self._parent)

        parent = self._parent
        msg = parent.message
        state = parent._state
        message_id = msg.id if msg else None
        if parent.type is not InteractionType.component:
            return

        payload = {}
        if content is not MISSING:
            if content is None:
                payload['content'] = None
            else:
                payload['content'] = str(content)

        if embed is not MISSING and embeds is not MISSING:
            raise TypeError('cannot mix both embed and embeds keyword arguments')

        if embed is not MISSING:
            if embed is None:
                embeds = []
            else:
                embeds = [embed]

        if embeds is not MISSING:
            payload['embeds'] = [e.to_dict() for e in embeds]

        if attachments is not MISSING:
            payload['attachments'] = [a.to_dict() for a in attachments]

        if view is not MISSING:
            state.prevent_view_updates_for(message_id)
            if view is None:
                payload['components'] = []
            else:
                payload['components'] = view.to_components()

        adapter = async_context.get()
        await adapter.create_interaction_response(
            parent.id,
            parent.token,
            session=parent._session,
            type=InteractionResponseType.message_update.value,
            data=payload,
        )

        if view and not view.is_finished():
            state.store_view(view, message_id)

        self._responded = True


class _InteractionMessageState:
    __slots__ = ('_parent', '_interaction')

    def __init__(self, interaction: Interaction, parent: ConnectionState):
        self._interaction: Interaction = interaction
        self._parent: ConnectionState = parent

    def _get_guild(self, guild_id):
        return self._parent._get_guild(guild_id)

    def store_user(self, data):
        return self._parent.store_user(data)

    def create_user(self, data):
        return self._parent.create_user(data)

    @property
    def http(self):
        return self._parent.http

    def __getattr__(self, attr):
        return getattr(self._parent, attr)


class InteractionMessage(Message):
    """Represents the original interaction response message.

    This allows you to edit or delete the message associated with
    the interaction response. To retrieve this object see :meth:`Interaction.original_message`.

    This inherits from :class:`discord.Message` with changes to
    :meth:`edit` and :meth:`delete` to work.

    .. versionadded:: 2.0
    """

    __slots__ = ()
    _state: _InteractionMessageState

    async def edit(
        self,
        content: Optional[str] = MISSING,
        embeds: List[Embed] = MISSING,
        embed: Optional[Embed] = MISSING,
        file: File = MISSING,
        files: List[File] = MISSING,
        view: Optional[View] = MISSING,
        allowed_mentions: Optional[AllowedMentions] = None,
    ) -> InteractionMessage:
        """|coro|

        Edits the message.

        Parameters
        ------------
        content: Optional[:class:`str`]
            The content to edit the message with or ``None`` to clear it.
        embeds: List[:class:`Embed`]
            A list of embeds to edit the message with.
        embed: Optional[:class:`Embed`]
            The embed to edit the message with. ``None`` suppresses the embeds.
            This should not be mixed with the ``embeds`` parameter.
        file: :class:`File`
            The file to upload. This cannot be mixed with ``files`` parameter.
        files: List[:class:`File`]
            A list of files to send with the content. This cannot be mixed with the
            ``file`` parameter.
        allowed_mentions: :class:`AllowedMentions`
            Controls the mentions being processed in this message.
            See :meth:`.abc.Messageable.send` for more information.
        view: Optional[:class:`~discord.ui.View`]
            The updated view to update this message with. If ``None`` is passed then
            the view is removed.

        Raises
        -------
        HTTPException
            Editing the message failed.
        Forbidden
            Edited a message that is not yours.
        TypeError
            You specified both ``embed`` and ``embeds`` or ``file`` and ``files``
        ValueError
            The length of ``embeds`` was invalid.

        Returns
        ---------
        :class:`InteractionMessage`
            The newly edited message.
        """
        return await self._state._interaction.edit_original_message(
            content=content,
            embeds=embeds,
            embed=embed,
            file=file,
            files=files,
            view=view,
            allowed_mentions=allowed_mentions,
        )

    async def delete(self, *, delay: Optional[float] = None) -> None:
        """|coro|

        Deletes the message.

        Parameters
        -----------
        delay: Optional[:class:`float`]
            If provided, the number of seconds to wait before deleting the message.
            The waiting is done in the background and deletion failures are ignored.

        Raises
        ------
        Forbidden
            You do not have proper permissions to delete the message.
        NotFound
            The message was deleted already.
        HTTPException
            Deleting the message failed.
        """

        if delay is not None:

            async def inner_call(delay: float = delay):
                await asyncio.sleep(delay)
                try:
                    await self._state._interaction.delete_original_message()
                except HTTPException:
                    pass

            asyncio.create_task(inner_call())
        else:
            await self._state._interaction.delete_original_message()

class InteractionContext:
    """Represents the context of an interaction usually in application commands.

    This class is passed in application command's callback function as first argument.

    Attributes
    ----------

    bot: :class:`~discord.Bot`
        The bot this interaction context belongs to.
    interaction: :class:`Interaction`
        The actual interaction this context belongs to.

    """
    def __init__(self, bot: Bot, interaction: Interaction) -> None:
        self.bot = bot
        self.interaction = interaction

    @property
    def channel(self) -> abc.Snowflake:
        """:class:`abc.Snowflake`: The channel in which interaction was made."""
        return self.interaction.channel

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild in which interaction was made. If applicable."""
        return self.interaction.guild

    @property
    def message(self) -> InteractionMessage:
        """:class:`InteractionMessage`: The original interaction response message."""
        return self.interaction.message

    @property
    def user(self) -> Union[Member, User]:
        """Union[:class:`Member`, :class:`User`]: The user who made the interaction."""
        return self.interaction.user

    author = user

    @property
    def response(self) -> InteractionResponse:
        """:class:`InteractionResponse`: The response of interaction."""
        return self.interaction.response

    # actions

    @property
    def respond(self) -> Callable:
        return self.interaction.response.send_message

    @property
    def send(self) -> Callable:
        return self.respond

    @property
    def defer(self) -> Callable:
        return self.interaction.response.defer

    @property
    def followup(self) -> Callable:
        return self.interaction.followup

# Application commands

class OptionChoice:
    """Represents an option choice for an application command's option.


    Attributes
    ----------

    name: :class:`str`
        The name of choice.
    value: :class:`str`
        The value of the choice.
    """
    @overload
    def __init__(self, *,
        name: str = ...,
        value: str = ...,
    ):
        ...

    def __init__(self, **data):
        self.name: str = data['name']
        self.value: str = data['value']

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'value': self.value,
        }

    def __repr__(self):
        return f'<OptionChoice name={self.name!r} value={self.value!r}'

    def __str__(self):
        return self.name


class Option:
    """Represents an option for an application slash command.

    Attributes
    ----------

    type: :class:`OptionType`
        The type of the option.
    name: :class:`str`
        The name of option.
    description: :class:`str`
        The description of option.
    required: :class:`bool`
        Whether this option is required or not.
    choices: List[:class:`OptionChoice`]
        The list of choices this option has.
    options: List[:class:`Option`]
        The options if the type is a subcommand or subcommand group.
    """
    def __init__(self, **data):
        try:
            self.type: OptionType = OptionType.from_datatype(data.get('type'))
        except TypeError:
            self.type: OptionType = data.get('type')

        self.name: str = data.get('name')
        self.description: str = data.get('description')
        self.required: bool = data.get('required', False)
        self.choices: List[OptionType] = data.get('choices', [])
        self.options: List[Option] = data.get('options', [])

    def __repr__(self):
        return f'<Option name={self.name!r} description={self.description!r}'

    def __str__(self):
        return self.name

    def is_command_or_group(self):
        """:class:`bool`: Indicates whether this option is a subcommand or subgroup."""
        return self.type in (
            OptionType.sub_command.value,
            OptionType.sub_command_group.value,
        )

    def add_choice(self, choice: OptionChoice) -> OptionChoice:
        """Adds a choice to current option.

        Parameters
        -----------

        choice: :class:`OptionChoice`
            The choice to add.
        """
        if not isinstance(choice, OptionChoice):
            raise TypeError('choice must be an instance of OptionChoice.')

        self.choices.append(choice)
        return choice

    def to_dict(self) -> dict:
        dict_ = {
            'type': self.type.value,
            'name': self.name,
            'description': self.description,
            'choices': [],
            'options': [],
        }
        if self.choices:
            dict_['choices'] = [choice.to_dict() for choice in self.choices]

        if self.options:
            dict_['options'] = [option.to_dict() for option in self.options]

        if not self.is_command_or_group():
            dict_['required'] = self.required

        return dict_


# TODO: Work on Application command permissions.


class ApplicationCommandPermissions:
    """Represents the permissions for an application command in a :class:`Guild`.

    Application commands permissions allow you to restrict a guild application command
    to a certain roles or users.

    Attributes
    ----------

    command_id: :class:`int`
        The ID of the command these permissions belong to.
    application_id: :class:`int`
        The ID of application this command belongs to.
    guild_id: :class:`int`
        The ID of the guild this command belongs to.
    permissions: List[:class:`ApplicationCommandPermissions`]
        The list that the commands hold in the guild.
    """
    __slots__ = (
        'command_id',
        'application_id',
        'guild_id',
        'permissions',
    )
    def __init__(self, data: ApplicationCommandPermissionsPayload):
        self.command_id: int = int(data['command_id'])
        self.application_id: int = int(data['application_id'])
        self.guild_id: int = int(data['guild_id'])
        self.permissions: ApplicationCommandPermission = (
            [ApplicationCommandPermission._from_data(perm)
            for perm in data.get('permissions', [])]
        )

class ApplicationCommandPermission:
    """A class representing a specific permission for an application command.

    The purpose of this class is to edit the commands permissions of a command in a guild.
    A number of parameters can be passed in this class initialization to customise
    the permissions.

    Parameters
    ----------

    role: :class:`~abc.Snowflake`
        The ID of role whose permission is defined. This cannot be mixed with ``user``
        parameter.
    user: :class:`~abc.Snowflake`
        The ID of role whose permission is defined. This cannot be mixed with ``role``
        parameter.
    permission: :class:`bool`
        The permission for the command. If this is set to ``False`` the provided
        user or role will not be able to use the command. Defaults to ``False``
    """
    def __init__(self, **options):
        self.user: abc.Snowflake = options.get('user')
        self.role: abc.Snowflake = options.get('role')

        if self.user is None and self.role is None:
            raise TypeError('at least one of role or user keyword parameter must be passed.')

        self.permission: abc.Snowflake = options.get('permission', False)

        if self.user:
            self._id = self.user.id
        elif self.role:
            self._id = self.role.id

    def to_dict(self):
        ret = {
            'id': self._id,
            'permission': self.permission
        }
        if self.user:
            ret['type'] = ApplicationCommandPermissionType.user.value
        elif self.role:
            ret['type'] = ApplicationCommandPermissionType.role.value

        return ret

class ApplicationCommand:
    """Represents an application command. This is base class for all application commands like
    slash commands, user commands etc.

    Attributes
    ----------

    callback: Callable
        The callback function for this command.
    name: :class:`str`
        The name of the command. Defaults to callback's name.
    description: :class:`str`
        The description of this command. Defaults to the docstring of the callback.
    guild_ids: Union[:class:`tuple`, :class:`list`]
        The guild this command will be registered in. Defaults to None for global commands.
    type: :class:`ApplicationCommandType`
        The type of application command.
    id: :class:`int`
        The ID of the command. This can be ``None``.
    application_id: :class:`int`
        The ID of the application command belongs to. This can be ``None``.
    default_permission: :class:`bool`
        Whether the command will be enabled by default or not when added to a guild.
    version: :class:`int`
        The version of command. Can be ``None``
    cog: :class:`diskord.ext.commands.Cog`
        The cog this command is defined in, This will be ``None`` if the command isn't
        defined in any cog.
    """

    def __init__(self, callback: Callable, **attrs):
        self.bot = attrs.get('bot')
        self.callback: Callable = callback
        self.name: str = attrs.get('name') or callback.__name__
        self.description: str = attrs.get('description') or self.callback.__doc__
        self.guild_ids: List[int] = attrs.get('guild_ids', [])
        self.cog = None

        if self.type in (
            ApplicationCommandType.user.value,
            ApplicationCommandType.message.value,
        ):
            # Message and User Commands do not have any description.
            # Ref: https://discord.com/developers/docs/interactions/application-commands#user-commands
            # Ref: https://discord.com/developers/docs/interactions/application-commands#message-commands

            self.description = ''

        self._from_data(attrs)

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
                value = context.bot.get_user(int(option['value']))

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

        if not interaction.data['type'] == self.type:
            raise TypeError(f'interaction type does not matches the command type. Interaction type is {interaction.data["type"]} and command type is {self.type}')

        if self.type == ApplicationCommandType.user.value:
            if interaction.guild:
                user = interaction.guild.get_member(int(interaction.data['target_id']))
            else:
                user = context.bot.get_user(int(interaction.data['target_id']))

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
                        state=context.bot._connection,
                        data=resolved['users'][interaction.data['target_id']]
                        )

            if self.cog is not None:
                await self.callback(self.cog, context, user)
            else:
                await self.callback(context, user)

            return

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
                    state=context.bot._connection,
                    channel=interaction.user,
                    data=data,
                )

            if self.cog is not None:
                await self.callback(self.cog, context, message)
            else:
                await self.callback(context, message)

            return



        options = interaction.data.get('options', [])
        kwargs = {}

        for option in options:
            if option['type'] == OptionType.sub_command.value:
                # We will use the name to get the child because
                # subcommands do not have any ID. They are essentially
                # just options of a command. And option names are unique

                sub_options = option.get('options', [])
                for sub_option in sub_options:
                    value = await self._parse_option(interaction, sub_option)
                    kwargs[sub_option['name']] = value

                subcommand = self.get_child(option['name'])

                if subcommand.cog is not None:
                    await subcommand.callback(subcommand.cog, context, **kwargs)
                else:
                    await subcommand.callback(context, **kwargs)

                return

            elif option['type'] == OptionType.sub_command_group.value:
                # In case of sub-command groups interactions, The options array
                # only has one element which is the subcommand that is being used
                # so we essentially just have to get the first element of the options
                # list and lookup the callback function for name of that element to
                # get the subcommand object.

                subcommand_raw = option['options'][0]
                group = self.get_child(option['name'])
                sub_options = subcommand_raw.get('options', [])

                for sub_option in sub_options:
                    value = await self._parse_option(interaction, sub_option)
                    kwargs[sub_option['name']] = value

                subcommand = group.get_child(subcommand_raw['name'])

                if subcommand.cog is not None:
                    await subcommand.callback(subcommand.cog, context, **kwargs)
                else:
                    await subcommand.callback(context, **kwargs)

                return

            else:
                value = await self._parse_option(interaction, option)
                kwargs[option['name']] = value

        if self.cog is not None:
            await self.callback(self.cog, context, **kwargs)
        else:
            await self.callback(context, **kwargs)



    def __repr__(self):
        # More attributes here?
        return f'<ApplicationCommand name={self.name!r} description={self.description!r} guild_ids={self.guild_ids!r}'

    def __str__(self):
        return self.name



    # TODO: Add to dict methods

    def _from_data(self, data: ApplicationCommandPayload) -> ApplicationCommand:
        self.id: int = utils._get_as_snowflake(data, 'id')
        self.application_id: int = utils._get_as_snowflake(data, 'application_id')
        self.guild_id: int = utils._get_as_snowflake(data, 'guild_id')
        self.default_permission: bool = data.get('default_permission')
        self.version: int = utils._get_as_snowflake(data, 'version')

        if 'name' in data:
            self.name = data.get('name')
        if 'description' in data:
            self.description = data.get('description')

        return self

class SlashSubCommandGroup(Option, SlashCommandChildMixin):
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

    Attributes
    ----------

    name: :class:`str`
        The name of command group.
    description: :class:`str`
        The description of command group.
    callback: Callable
        The callback for this command group.
    parent: :class:`SlashCommand`
        The parent command for this group.
    children: List[:class:`SlashSubCommand`]
        The list of commands this subcommand group holds.
    guild_ids: List[:class:`int`]
        A short-hand for :attr:`parent.guild_ids`

        Changing this will have no affect as the guild for a sub-command
        depend upon the guilds of parent command.
    """
    def __init__(self, callback: Callable, parent: SlashCommand, **attrs):
        self.callback = callback
        self.parent = parent
        self.children = []
        super().__init__(
            name=callback.__name__ or attrs.get('name'),
            description=callback.__doc__ or attrs.get('description'),
            type=OptionType.sub_command_group.value,
        )
        self._from_data = parent._from_data

    # parent attributes

    @property
    def guild_ids(self) -> List[int]:
        """List[:class:`int`]: Returns the list of guild IDs in which the parent command is registered."""
        return self.parent.guild_ids

    @property
    def cog(self):
        """Optional[:class:`diskord.ext.commands.Cog`]: Returns the cog of the parent. If parent has no cog, Then None is returned."""
        return self.parent.cog

    # children management

    def get_child(self, name: str, /):
        """
        Gets a child of this command i.e a subcommand or subcommand group of this command
        by the child's name.

        Returns ``None`` if the child is not found.

        Parameters
        ----------
        name: :class:`str`
            The name of the child.

        Returns
        -------
        Union[:class:`SlashSubCommand`, :class:`SlashSubGroup`]
            The required slash subcommand or subcommand group.
        """
        return (utils.get(self.children, name=name))

    def add_child(self, child: SlashSubCommand, /):
        """
        Adds a child i.e subcommand to the command group.

        This shouldn't generally be used. Instead, :func:`sub_command` decorator
        should be used.

        Parameters
        ----------

        child: :class:`SlashSubCommand`
            The child to add.
        """
        self.options.append(child)
        self.children.append(child)

        for opt in child.callback.__annotations__:
            child.add_option(child.callback.__annotations__[opt])

        return child

    def remove_child(self, child: Union[str, SlashSubCommand], /):
        """Removes a child like sub-command or sub-command group from the command.

        Parameters
        ----------

        child: Union[:class:`str`, :class:`SlashSubCommand`]
            The child to remove.
        """
        if isinstance(child, str):
            child = utils.get(self.children, name=child)

        try:
            self.children.remove(child)
        except ValueError:
            return


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
        """
        def inner(func: Callable):
            return self.add_child(SlashSubCommand(func, self, **attrs))

        return inner

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'type': OptionType.sub_command_group.value,
            'options': [option.to_dict() for option in self.options],
        }



class SlashSubCommand(Option):
    """Represents a subcommand of a slash command.

    This can be registered using :func:`SlashCommand.sub_command` decorator.

    Example: ::

        @bot.slash_command(description='A cool command that has subcommands.')
        async def git(ctx):
            pass

        @git.sub_command(description='This is git push!')
        async def push(ctx):
            await ctx.send('Pushed!')

    The usage of above command would be like ``/git push``.

    Attributes
    ----------

    name: :class:`str`
        The name of sub-command.
    description: :class:`str`
        The description of sub-command.
    options: List[:class:`Option`]
        The options of sub-command.
    callback: Callable
        The callback for this sub-command.
    parent: :class:`SlashCommand`
        The parent command for this sub-command.
    guild_ids: List[:class:`int`]
        A short-hand for :attr:`parent.guild_ids`

        Changing this will have no affect as the guild for a sub-command
        depend upon the guilds of parent command.
    """
    def __init__(self, callback: Callable, parent: SlashCommand, **attrs):
        self.callback = callback
        self.parent = parent
        super().__init__(
            name=callback.__name__ or attrs.get('name'),
            description=callback.__doc__ or attrs.get('description'),
            type=OptionType.sub_command.value,
        )

        self._from_data = parent._from_data

    # parent attributes

    @property
    def guild_ids(self) -> List[int]:
        """List[:class:`int`]: Returns the list of guild IDs in which the parent command is registered."""
        return self.parent.guild_ids

    @property
    def cog(self):
        """Optional[:class:`diskord.ext.commands.Cog`]: Returns the cog of the parent. If parent has no cog, Then None is returned."""
        return self.parent.cog

    def to_dict(self) -> dict:
        options = self.options
        options.reverse()

        dict_ = {
            'name': self.name,
            'description': self.description,
            'type': OptionType.sub_command.value,
            'options': [option.to_dict() for option in options],
        }
        return dict_

    def add_option(self, option: Option) -> Option:
        """Adds an option to this slash command.

        Parameters
        ----------
        option: :class:`Option`
            The option to add.

        Returns
        -------
        :class:`Option`
            The added option.

        """
        if not isinstance(option, Option):
            raise TypeError('option must be an instance of Option class.')

        self.options.append(option)
        return option



class SlashCommand(ApplicationCommand, SlashCommandChildMixin):
    """Represents a slash command.

    A slash command is a user input command that a user can use by typing ``/`` in
    the chat.

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.slash`
    """
    def __init__(self, callback, **attrs):
        self.type = ApplicationCommandType.slash.value
        self.options: List[Option] = []
        self.children: List[SubSlashCommand, SubSlashGroup] = []

        # To stay consistent with the discord.ext.commands models, I added this
        # parent attribute here which will always be None in case of this.
        self.parent = None

        super().__init__(callback, **attrs)


    def add_option(self, option: Option) -> Option:
        """Adds an option to this slash command.

        Parameters
        ----------
        option: :class:`Option`
            The option to add.

        Returns
        -------
        :class:`Option`
            The added option.

        """
        if not isinstance(option, Option):
            raise TypeError('option must be an instance of Option class.')

        self.options.append(option)
        return option

    # children management

    def get_child(self, name: str, /):
        """
        Gets a child of this command i.e a subcommand or subcommand group of this command
        by the child's name.

        Returns ``None`` if the child is not found.

        Parameters
        ----------
        name: :class:`str`
            The name of the child.

        Returns
        -------
        Union[:class:`SlashSubCommand`, :class:`SlashSubGroup`]
            The required slash subcommand or subcommand group.
        """
        return (utils.get(self.children, name=name))

    def add_child(self, child: SlashSubCommand, /):
        """
        Adds a child i.e subcommand to the command group.

        This shouldn't generally be used. Instead, :func:`sub_command` decorator
        should be used.

        Parameters
        ----------

        child: :class:`SlashSubCommand`
            The child to add.
        """
        self.options.append(child)
        self.children.append(child)

        for opt in child.callback.__annotations__:
            child.add_option(child.callback.__annotations__[opt])

        return child

    def remove_child(self, child: Union[str, SlashSubCommand], /):
        """Removes a child like sub-command or sub-command group from the command.

        Parameters
        ----------

        child: Union[:class:`str`, :class:`SlashSubCommand`]
            The child to remove.
        """
        if isinstance(child, str):
            child = utils.get(self.children, name=child)

        try:
            self.children.remove(child)
        except ValueError:
            return


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
            return self.add_child(SlashSubCommand(func, self, **attrs))

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
            return self.add_child(SlashSubCommandGroup(func, self, **attrs))

        return inner

    def to_dict(self) -> dict:
        # We're reversing the options list here because the order of how options are
        # registered using decorator is below-to-top so we have to reverse it to
        # normalize the list. The core reason is that discord API does not
        # allow to put the non-required options before required ones which makes sense.

        reversed_options = self.options
        reversed_options.reverse()

        dict_ = {
            'name': self.name,
            'type': self.type,
            'options': [option.to_dict() for option in reversed_options],
            'description': self.description,
        }

        return dict_


class UserCommand(ApplicationCommand):
    """Represents a user command.

    A user command can be used by right-clicking a user in discord and choosing the
    command from "Apps" context menu

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.user`
    """
    def __init__(self, callback, **attrs):
        self.type = ApplicationCommandType.user.value
        super().__init__(callback, **attrs)


    def to_dict(self) -> dict:
        dict_ = {
            'name': self.name,
            'description': self.description,
            'type': self.type,
        }
        return dict_

class MessageCommand(ApplicationCommand):
    """Represents a message command.

    A message command can be used by right-clicking a message in discord and choosing
    the command from "Apps" context menu.

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.

    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.message`
    """
    def __init__(self, callback, **attrs):
        self.type = ApplicationCommandType.message.value
        super().__init__(callback, **attrs)


    def to_dict(self) -> dict:
        dict_ = {
            'name': self.name,
            'description': self.description,
            'type': self.type,
        }
        return dict_
