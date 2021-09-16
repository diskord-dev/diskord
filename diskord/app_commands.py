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
    Callable,
)
from .utils import _get_as_snowflake
from .enums import (
    try_enum,
    ApplicationCommandType,
    OptionType,
)

if TYPE_CHECKING:
    from .types.interactions import (
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
    def __init__(self, **data):
        if isinstance(data.get('type'), type):
            self.type: OptionType = OptionType.from_datatype(data.get('type'))
        else:
            self.type: OptionType = data.get('type')

        self.name: str = data['name']
        self.description: str = data['description']
        self.required: bool = data.get('required', False)
        self.choices: List[OptionType] = [OptionType(choice) for choice in data.get('choices', [])]
        self.options: List[Option] = [Option(option) for option in data.get('options', [])]

    def __repr__(self):
        return f'<Option name={self.name!r} description={self.description!r}'

    def __str__(self):
        return self.name
    
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
            'required': self.required,
            'choices': [],
            'options': [],
        }
        if self.choices:
            dict_['choices'] = [choice.to_dict() for choice in self.choices]
        
        if self.options:
            dict_['options'] = [option.to_dict() for option in self.options]
        
        return dict_
            

class ApplicationCommand:
    """Represents an application command. This is base class for all application commands like
    slash commands, user commands etc.

    Attributes
    ----------

    callback: Callable
        The callback for this command.
    name: :class:`str`
        The name of the command. Defaults to callback's name.
    description: :class:`str`
        The description of this command. Defaults to the docstring of the callback.
    guild_ids: Union[:class:`tuple`, :class:`list`]
        The guild this command will be registered in. Defaults to None for global commands.

    """

    def __init__(self, callback: Callable, **attrs):
        self.callback: Callable = callback
        self.name: str = attrs.get('name') or callback.__name__
        self.description: str = attrs.get('description') or self.callback.__doc__
        self.guild_ids = attrs.get('guild_ids', None)

        if self.type in (
            ApplicationCommandType.user.value,
            ApplicationCommandType.message.value,
        ):
            # Message and User Commands do not have any description.
            # Ref: https://discord.com/developers/docs/interactions/application-commands#user-commands
            # Ref: https://discord.com/developers/docs/interactions/application-commands#message-commands
            
            self.description = '' # type: ignore

    def __repr__(self):
        # More attributes here?
        return f'<ApplicationCommand name={self.name!r} description={self.description!r} guild_ids={self.guild_ids!r}'
    
    def __str__(self):
        return self.name
    

    
    # TODO: Add to dict methods

    def _from_data(self, data: ApplicationCommandPayload) -> ApplicationCommand:
        self.id: int = _get_as_snowflake(data, 'id')
        self.type: int = try_enum(ApplicationCommandType, int(data['type']))
        self.application_id: int = _get_as_snowflake(data, 'application_id')
        self.guild_id: int = _get_as_snowflake(data, 'guild_id')
        self.default_permission: bool = data.get('default_permission')
        self.version: int = _get_as_snowflake(data, 'version') 
        
        return self


class SlashCommand(ApplicationCommand):
    """Represents a slash command.
    
    A slash command is a user input command that a user can use by typing ``/`` in
    the chat.

    This class inherits from :class:`ApplicationCommand` so all attributes valid
    there are valid here too.
    
    In this class, The ``type`` attribute will always be :attr:`ApplicationCommandType.slash`
    """
    def __init__(self, callback, **attrs):
        self.type = ApplicationCommandType.slash.value
        self.options: List[Option] = attrs.get('options', [])
        super().__init__(callback, **attrs)
    
        if not self.description:
            raise TypeError('description for slash commands is required.')
    
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

    
    def to_dict(self) -> dict:
        dict_ = {
            'name': self.name,
            'type': self.type,
            "options": [option.to_dict() for option in self.options],
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
            'description': '',
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
            'description': '',
            'type': self.type,
        }
        return dict_