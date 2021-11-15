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
from typing import TYPE_CHECKING

from . import utils
from .enums import EntityType, EventPrivacyLevel, EventStatus, try_enum

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

        md = data.get('entity_metadata')
        if md:
            self._unroll_metadata(md)

        self.privacy_level: EventPrivacyLevel = try_enum(EventPrivacyLevel, int(data['privacy_level']))
        self.status: EventStatus = try_enum(EventStatus, int(data['status']))
        self.entity_type: EntityType = try_enum(EntityType, int(data['entity_type']))

    def _unroll_metadata(self, data: EntityMetadata):
        self.speaker_ids: List[int] = [int(i) for i in data.get('speaker_ids', [])]
        self.location: str = data.get('location')
