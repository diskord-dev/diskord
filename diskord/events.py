# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz, 2021-present NerdGuyAhmad

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
from typing import TYPE_CHECKING, Optional, Union

from . import utils
from .enums import EntityType, EventPrivacyLevel, EventStatus, try_enum
from .channel import StageChannel, VoiceChannel

if TYPE_CHECKING:
    from .guild import Guild
    from .types.events import (
        ScheduledEvent as ScheduledEventPayload,
        EntityMetadata
    )


class ScheduledEvent:
    """Represents a scheduled event in a :class:`Guild`.

    Attributes
    ----------
    id: :class:`int`
        The ID of this event.
    guild: :class:`Guild`
        The guild that this event is scheduled in.
    channel_id: Optional[:class:`int`]
        The ID of channel that this event is scheduled in, Could be None.
    creator_id: :class:`int`
        The ID of creator of this event.
    entity_id: Optional[:class:`int`]
        The additional and optional hosting place ID e.g :class:`StageInstance.id`
    name: :class:`str`
        The title of this event.
    description: Optional[:class:`str`]
        The description of this event.
    user_count: :class:`int`
        The number of users that have subscribed to this event. This is not available in cases
        when the event was fetched with ``with_user_counts`` set to False.
    starts_at: :class:`datetime.datetime`
        The datetime representation of the time when this event starts.
    ends_at: Optional[:class:`datetime.datetime`]
        The datetime representation of the time when this event ends or None if no
        schedule is set for ending time.
    speaker_ids: List[:class:`int`]
        List of IDs of users that will be speaking in stage.
    location: Optional[:class:`str`]
        The external location name where the event is being hosted.
    """
    __slots__ = (
        'guild', '_state', 'id', 'channel_id', 'creator_id', 'entity_id', 'name',
        'description', 'user_count', 'starts_at', 'ends_at', 'privacy_level', 'status',
        'entity_type', 'speaker_ids', 'location'
    )
    def __init__(self, data: ScheduledEventPayload, guild: Guild):
        self.guild = guild
        self._state = guild._state
        self._update(data)

    def _update(self, data: ScheduledEventPayload):
        self.id: int = int(data['id']) # type: ignore
        self.channel_id: Optional[int] = utils._get_as_snowflake(data, 'channel_id')
        self.creator_id: Optional[int] = utils._get_as_snowflake(data, 'creator_id')
        self.entity_id: Optional[int] = utils._get_as_snowflake(data, 'entity_id')
        self.name: str = data.get('name')
        self.description: Optional[str] = data.get('description')
        self.user_count: Optional[int] = data.get('user_count')

        self.starts_at: datetime.datetime = utils.parse_time(data.get('scheduled_start_time')) # type: ignore
        self.ends_at: Optional[datetime.datetime] = utils.parse_time(data.get('scheduled_end_time')) # type: ignore

        self.privacy_level: EventPrivacyLevel = try_enum(EventPrivacyLevel, int(data['privacy_level']))
        self.status: EventStatus = try_enum(EventStatus, int(data['status']))
        self.entity_type: EntityType = try_enum(EntityType, int(data['entity_type']))

        md = data.get('entity_metadata')
        if md:
            self._unroll_metadata(md)

    def _unroll_metadata(self, data: EntityMetadata):
        self.speaker_ids: List[int] = [int(i) for i in data.get('speaker_ids', [])]
        self.location: Optional[str] = data.get('location')

    @property
    def creator(self) -> Optional[Member]:
        """
        Optional[:class:`Member`]: The member who created this event. If member has left the
        guild then this would be None.
        """
        return self.guild.get_member(self.creator_id) # type: ignore

    @property
    def channel(self) -> GuildChannel:
        """
        Optional[:class:`abc.GuildChannel`]: The channel where event is hosted only
        available if the event is not externally hosted.
        """
        return self.guild.get_channel(self.channel_id)

    async def delete(self):
        """|coro|

        Deletes the scheduled event.

        This requires :attr:`~Permissions.manage_events` permission to work.

        Raises
        --------
        HTTPException
            Deleting the event failed.
        Forbidden
            You do not have permissions to delete the event.
        """
        await self._state.http.delete_scheduled_event(
            guild_id=self.guild.id,
            event_id=self.id,
        )
        return self

    async def edit(self, *,
        name: Optional[str] = None,
        starts_at: Optional[datetime.datetime] = None,
        ends_at: Optional[datetime.datetime] = None,
        description: Optional[str] = None,
        entity_type: Optional[EntityType] = None,
        privacy_level: EventPrivacyLevel = EventPrivacyLevel.guild_only,
        channel: Optional[Union[VoiceChannel, StageChannel]] = None,
        location: Optional[str] = None,
        status: Optional[EventStatus] = None,
        ):
        """|coro|

        Edit the scheduled event.

        This requires :attr:`~Permissions.manage_events` permission to work.

        Parameters
        ----------
        name: :class:`str`
            The name of event.
        starts_at: :class:`datetime.datetime`
            The scheduled time when the event would start.
        ends_at: :class:`datetime.datetime`
            The scheduled time when the event would end.
        description: :class:`str`
            The description of event.
        entity_type: :class:`EntityType`
            The type of entity where event is hosted.
        privacy_level: :class:`EventPrivacyLevel`
            The privacy level of this event. Defaults to :attr:`EventPrivacyLevel.guild_only`
        channel: Union[:class:`VoiceChannel`, :class:`StageChannel`]
            The channel that this event would be hosted in.
        location: :class:`str`
            External location of event if it is externally hosted.

        Raises
        --------
        HTTPException
            Editing the event failed.
        Forbidden
            You do not have permissions to edit the event.
        """
        if location is not None and channel is not None:
            raise TypeError('location and channel keyword arguments cannot be mixed.')

        payload = {}

        if name is not None:
            payload['name'] = str(name)
        if starts_at is not None:
            payload['scheduled_start_time'] = starts_at.isoformat()
        if ends_at is not None:
            payload['scheduled_end_time'] = ends_at.isoformat()
        if description is not None:
            payload['description'] = str(description)
        if entity_type is not None:
            payload['entity_type'] = entity_type.value
        elif entity_type is None:
            if location is not None:
                entity_type = EntityType.external
            elif isinstance(channel, StageChannel):
                entity_type = EntityType.stage_instance
            elif isinstance(channel, VoiceChannel):
                entity_type = EntityType.voice
            if entity_type:
                payload['entity_type'] = entity_type.value

        if privacy_level is not None:
            payload['privacy_level'] = privacy_level.value
        if channel is not None:
            payload['channel_id'] = channel.id
        if location is not None:
            payload['entity_metadata'] = {}
            payload['entity_metadata']['location'] = location
        if status is not None:
            payload['status'] = status.value

        data = await self._state.http.edit_scheduled_event(
            guild_id=self.guild.id,
            event_id=self.id,
            payload=payload,
        )
        return ScheduledEvent(data, guild=self.guild)

    async def start(self):
        """|coro|

        Starts the event.

        This only works if :attr:`.status` is currently :attr:`EventStatus.scheduled`

        Raises
        --------
        HTTPException
            Event has either been completed or is active already.
        Forbidden
            You do not have permissions to start the event.
        """
        await self.edit(status=EventStatus.active)

    async def end(self):
        """|coro|

        Ends the event.

        This only works if :attr:`.status` is currently :attr:`EventStatus.active`

        Raises
        --------
        HTTPException
            Event has either been completed already or is not active.
        Forbidden
            You do not have permissions to end the event.
        """
        await self.edit(status=EventStatus.completed)

    async def cancel(self):
        """|coro|

        Cancels the event.

        Raises
        --------
        HTTPException
            Cancellation failed.
        Forbidden
            You do not have permissions to cancel the event.
        """
        await self.edit(status=EventStatus.canceled)

