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
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    Union,
)
from .utils import _get_as_snowflake
from .enums import (
    try_enum,
    ApplicationCommandType,
    OptionType,
)

if TYPE_CHECKING:
    from .types.app_commands import (
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        ApplicationCommandOptionChoice as ApplicationCommandOptionChoicePayload,
    )

class OptionChoice:
    """Represents an option choice for an application command's option.


    Attributes
    ----------

    name: :class:`str`
        The name of choice.
    value: Union[:class:`str`, :class:`int`, :class:`float`]
        The value of the choice.
    """
    def __init__(self, data: ApplicationCommandOptionChoicePayload):
        self.name: str = data['name']
        self.value: Union[str, int, float] = data['value']
    
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
    def __init__(self, data: ApplicationCommandOptionPayload):
        self.type: OptionType = try_enum(OptionType, int(data['type']))
        self.name: str = data['name']
        self.description: str = data['description']
        self.required: bool = data.get('required', False)
        self.choices: Any = data.get('choices', []) # TODO: Proper typehint when choices are implemented.
        self.options: List[Option] = [Option(option) for option in data.get('options', [])]

    def __repr__(self):
        return f'<Option name={self.name!r} description={self.description!r}'

    def __str__(self):
        return self.name

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
    options: Optional[List[:class:`Option`]]
        The list of options this command has.
    default_permission: :class:`bool`
        Whether the command is enabled by default when the app is added to a guild.
    version: :class:`int`
        Auto incrementing version identifier updated during substantial record changes.
    """

    def __init__(self, data: ApplicationCommandPayload):
        self.id: int = int(data['id'])
        self.type: ApplicationCommandType = try_enum(ApplicationCommandType, int(data['type']))
        self.application_id: int = int(data['application_id'])
        self.guild_id: Optional[int] = _get_as_snowflake(data.get('guild_id'))
        self.name: str = data['name']
        self.description: str = data['description']
        self.options: List[Option] = [
            Option(option) for option in data.get('options', [])
            ]
        self.default_permission: bool = data['bool']
        self.version: int = int(data['version'])

    def __repr__(self):
        # More attributes here?
        return f'<ApplicationCommand name={self.name!r} description={self.description!r}'
    
    def __str__(self):
        return self.name