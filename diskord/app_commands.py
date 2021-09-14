"""
The MIT License (MIT)

Copyright (c) 2015-present NerdGuyAhmad

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

class ApplicationCommand:
    """Represents an application command.

    Attributes
    ----------

    id: :class:`int`
        The ID of application command.
    type: :class:`ApplicationCommandType`
        The type of application command.
    application_id: :class:`int`
        The ID of application this command belongs.
    guild_id: Optional[:class:`int`]
        The ID of guild this command is registered in, This is None if the command
        is global.
    name: :class:`str`
        The name of command.
    description: :class:`str`
        The description of command.
    options: List[:class:`ApplicationCommandOptionType`]
        The list of options this command has.
    default_permission: :class:`bool`
        Whether the command is enabled by default when the app is added to a guild.
    version: :class:`int`
        Auto incrementing version identifier updated during substantial record changes.
    """
    # TODO