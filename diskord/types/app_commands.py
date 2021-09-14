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
    List, 
    Literal,
    Optional, 
    TypedDict,
    Union,
)

from .snowflake import Snowflake

class ApplicationCommandOptionChoice(TypedDict, total=False):
    name: str
    value: Union[str, int, float]

class _ApplicationCommandOptionOptional(TypedDict, total=False):
    required: bool
    choices: List[ApplicationCommandOptionChoice]
    options: List[ApplicationCommandOption]

class ApplicationCommandOption(_ApplicationCommandOptional):
    type: int
    name: str
    description: str

class _ApplicationCommandOptional(TypedDict, total=False):
    type: Union[Literal[1], Literal[2], Literal[3]]
    guild_id: Snowflake
    options: Any # TODO: Add proper type when options are implemented

class ApplicationCommand(_ApplicationCommandOptional):
    id: Snowflake
    application_id: Snowflake
    name: str
    description: str
    default_permission: bool
    version: int

