.. currentmodule:: diskord

API Reference
===============

The following section outlines the API of diskord's command extension module.

.. _ext_commands_api_bot:

Bots
------

Bot
~~~~

.. attributetable:: diskord.ext.commands.Bot

.. autoclass:: diskord.ext.commands.Bot
    :members:
    :inherited-members:
    :exclude-members: after_invoke, before_invoke, check, check_once, command, event, group, listen

    .. automethod:: Bot.after_invoke()
        :decorator:

    .. automethod:: Bot.before_invoke()
        :decorator:

    .. automethod:: Bot.check()
        :decorator:

    .. automethod:: Bot.check_once()
        :decorator:

    .. automethod:: Bot.command(*args, **kwargs)
        :decorator:
    
    .. automethod:: Bot.event()
        :decorator:

    .. automethod:: Bot.group(*args, **kwargs)
        :decorator:

    .. automethod:: Bot.listen(name=None)
        :decorator:

AutoShardedBot
~~~~~~~~~~~~~~~~

.. attributetable:: diskord.ext.commands.AutoShardedBot

.. autoclass:: diskord.ext.commands.AutoShardedBot
    :members:

Prefix Helpers
----------------

.. autofunction:: diskord.ext.commands.when_mentioned

.. autofunction:: diskord.ext.commands.when_mentioned_or

.. _ext_commands_api_events:

Event Reference
-----------------

These events function similar to :ref:`the regular events <discord-api-events>`, except they
are custom to the command extension module.

.. function:: diskord.ext.commands.on_command_error(ctx, error)

    An error handler that is called when an error is raised
    inside a command either through user input error, check
    failure, or an error in your own code.

    A default one is provided (:meth:`.Bot.on_command_error`).

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`
    :param error: The error that was raised.
    :type error: :class:`.CommandError` derived

.. function:: diskord.ext.commands.on_command(ctx)

    An event that is called when a command is found and is about to be invoked.

    This event is called regardless of whether the command itself succeeds via
    error or completes.

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`

.. function:: diskord.ext.commands.on_command_completion(ctx)

    An event that is called when a command has completed its invocation.

    This event is called only if the command succeeded, i.e. all checks have
    passed and the user input it correctly.

    :param ctx: The invocation context.
    :type ctx: :class:`.Context`

.. _ext_commands_api_command:

Commands
----------

Decorators
~~~~~~~~~~~~

.. autofunction:: diskord.ext.commands.command
    :decorator:

.. autofunction:: diskord.ext.commands.group
    :decorator:

Command
~~~~~~~~~

.. attributetable:: diskord.ext.commands.Command

.. autoclass:: diskord.ext.commands.Command
    :members:
    :special-members: __call__
    :exclude-members: after_invoke, before_invoke, error

    .. automethod:: Command.after_invoke()
        :decorator:

    .. automethod:: Command.before_invoke()
        :decorator:

    .. automethod:: Command.error()
        :decorator:

Group
~~~~~~

.. attributetable:: diskord.ext.commands.Group

.. autoclass:: diskord.ext.commands.Group
    :members:
    :inherited-members:
    :exclude-members: after_invoke, before_invoke, command, error, group

    .. automethod:: Group.after_invoke()
        :decorator:

    .. automethod:: Group.before_invoke()
        :decorator:

    .. automethod:: Group.command(*args, **kwargs)
        :decorator:

    .. automethod:: Group.error()
        :decorator:

    .. automethod:: Group.group(*args, **kwargs)
        :decorator:

GroupMixin
~~~~~~~~~~~

.. attributetable:: diskord.ext.commands.GroupMixin

.. autoclass:: diskord.ext.commands.GroupMixin
    :members:
    :exclude-members: command, group

    .. automethod:: GroupMixin.command(*args, **kwargs)
        :decorator:

    .. automethod:: GroupMixin.group(*args, **kwargs)
        :decorator:

.. _ext_commands_api_cogs:

Cogs
------

Cog
~~~~

.. attributetable:: diskord.ext.commands.Cog

.. autoclass:: diskord.ext.commands.Cog
    :members:

CogMeta
~~~~~~~~

.. attributetable:: diskord.ext.commands.CogMeta

.. autoclass:: diskord.ext.commands.CogMeta
    :members:

.. _ext_commands_help_command:

Help Commands
---------------

HelpCommand
~~~~~~~~~~~~

.. attributetable:: diskord.ext.commands.HelpCommand

.. autoclass:: diskord.ext.commands.HelpCommand
    :members:

DefaultHelpCommand
~~~~~~~~~~~~~~~~~~~

.. attributetable:: diskord.ext.commands.DefaultHelpCommand

.. autoclass:: diskord.ext.commands.DefaultHelpCommand
    :members:
    :exclude-members: send_bot_help, send_cog_help, send_group_help, send_command_help, prepare_help_command

MinimalHelpCommand
~~~~~~~~~~~~~~~~~~~

.. attributetable:: diskord.ext.commands.MinimalHelpCommand

.. autoclass:: diskord.ext.commands.MinimalHelpCommand
    :members:
    :exclude-members: send_bot_help, send_cog_help, send_group_help, send_command_help, prepare_help_command

Paginator
~~~~~~~~~~

.. attributetable:: diskord.ext.commands.Paginator

.. autoclass:: diskord.ext.commands.Paginator
    :members:

Enums
------

.. class:: BucketType
    :module: diskord.ext.commands

    Specifies a type of bucket for, e.g. a cooldown.

    .. attribute:: default

        The default bucket operates on a global basis.
    .. attribute:: user

        The user bucket operates on a per-user basis.
    .. attribute:: guild

        The guild bucket operates on a per-guild basis.
    .. attribute:: channel

        The channel bucket operates on a per-channel basis.
    .. attribute:: member

        The member bucket operates on a per-member basis.
    .. attribute:: category

        The category bucket operates on a per-category basis.
    .. attribute:: role

        The role bucket operates on a per-role basis.

        .. versionadded:: 1.3


.. _ext_commands_api_checks:

Checks
-------

.. autofunction:: diskord.ext.commands.check(predicate)
    :decorator:

.. autofunction:: diskord.ext.commands.check_any(*checks)
    :decorator:

.. autofunction:: diskord.ext.commands.has_role(item)
    :decorator:

.. autofunction:: diskord.ext.commands.has_permissions(**perms)
    :decorator:

.. autofunction:: diskord.ext.commands.has_guild_permissions(**perms)
    :decorator:

.. autofunction:: diskord.ext.commands.has_any_role(*items)
    :decorator:

.. autofunction:: diskord.ext.commands.bot_has_role(item)
    :decorator:

.. autofunction:: diskord.ext.commands.bot_has_permissions(**perms)
    :decorator:

.. autofunction:: diskord.ext.commands.bot_has_guild_permissions(**perms)
    :decorator:

.. autofunction:: diskord.ext.commands.bot_has_any_role(*items)
    :decorator:

.. autofunction:: diskord.ext.commands.cooldown(rate, per, type=diskord.ext.commands.BucketType.default)
    :decorator:

.. autofunction:: diskord.ext.commands.dynamic_cooldown(cooldown, type=BucketType.default)
    :decorator:

.. autofunction:: diskord.ext.commands.max_concurrency(number, per=diskord.ext.commands.BucketType.default, *, wait=False)
    :decorator:

.. autofunction:: diskord.ext.commands.before_invoke(coro)
    :decorator:

.. autofunction:: diskord.ext.commands.after_invoke(coro)
    :decorator:

.. autofunction:: diskord.ext.commands.guild_only(,)
    :decorator:

.. autofunction:: diskord.ext.commands.dm_only(,)
    :decorator:

.. autofunction:: diskord.ext.commands.is_owner(,)
    :decorator:

.. autofunction:: diskord.ext.commands.is_nsfw(,)
    :decorator:

.. _ext_commands_api_context:

Cooldown
---------

.. attributetable:: diskord.ext.commands.Cooldown

.. autoclass:: diskord.ext.commands.Cooldown
    :members:

Context
--------

.. attributetable:: diskord.ext.commands.Context

.. autoclass:: diskord.ext.commands.Context
    :members:
    :inherited-members:
    :exclude-members: history, typing

    .. automethod:: diskord.ext.commands.Context.history
        :async-for:

    .. automethod:: diskord.ext.commands.Context.typing
        :async-with:

.. _ext_commands_api_converters:

Converters
------------

.. autoclass:: diskord.ext.commands.Converter
    :members:

.. autoclass:: diskord.ext.commands.ObjectConverter
    :members:

.. autoclass:: diskord.ext.commands.MemberConverter
    :members:

.. autoclass:: diskord.ext.commands.UserConverter
    :members:

.. autoclass:: diskord.ext.commands.MessageConverter
    :members:

.. autoclass:: diskord.ext.commands.PartialMessageConverter
    :members:

.. autoclass:: diskord.ext.commands.GuildChannelConverter
    :members:

.. autoclass:: diskord.ext.commands.TextChannelConverter
    :members:

.. autoclass:: diskord.ext.commands.VoiceChannelConverter
    :members:

.. autoclass:: diskord.ext.commands.StoreChannelConverter
    :members:

.. autoclass:: diskord.ext.commands.StageChannelConverter
    :members:

.. autoclass:: diskord.ext.commands.CategoryChannelConverter
    :members:

.. autoclass:: diskord.ext.commands.InviteConverter
    :members:

.. autoclass:: diskord.ext.commands.GuildConverter
    :members:

.. autoclass:: diskord.ext.commands.RoleConverter
    :members:

.. autoclass:: diskord.ext.commands.GameConverter
    :members:

.. autoclass:: diskord.ext.commands.ColourConverter
    :members:

.. autoclass:: diskord.ext.commands.EmojiConverter
    :members:

.. autoclass:: diskord.ext.commands.PartialEmojiConverter
    :members:

.. autoclass:: diskord.ext.commands.ThreadConverter
    :members:

.. autoclass:: diskord.ext.commands.GuildStickerConverter
    :members:

.. autoclass:: diskord.ext.commands.clean_content
    :members:

.. autoclass:: diskord.ext.commands.Greedy()

.. autofunction:: diskord.ext.commands.run_converters

Flag Converter
~~~~~~~~~~~~~~~

.. autoclass:: diskord.ext.commands.FlagConverter
    :members:

.. autoclass:: diskord.ext.commands.Flag()
    :members:

.. autofunction:: diskord.ext.commands.flag

.. _ext_commands_api_errors:

Exceptions
-----------

.. autoexception:: diskord.ext.commands.CommandError
    :members:

.. autoexception:: diskord.ext.commands.ConversionError
    :members:

.. autoexception:: diskord.ext.commands.MissingRequiredArgument
    :members:

.. autoexception:: diskord.ext.commands.ArgumentParsingError
    :members:

.. autoexception:: diskord.ext.commands.UnexpectedQuoteError
    :members:

.. autoexception:: diskord.ext.commands.InvalidEndOfQuotedStringError
    :members:

.. autoexception:: diskord.ext.commands.ExpectedClosingQuoteError
    :members:

.. autoexception:: diskord.ext.commands.BadArgument
    :members:

.. autoexception:: diskord.ext.commands.BadUnionArgument
    :members:

.. autoexception:: diskord.ext.commands.BadLiteralArgument
    :members:

.. autoexception:: diskord.ext.commands.PrivateMessageOnly
    :members:

.. autoexception:: diskord.ext.commands.NoPrivateMessage
    :members:

.. autoexception:: diskord.ext.commands.CheckFailure
    :members:

.. autoexception:: diskord.ext.commands.CheckAnyFailure
    :members:

.. autoexception:: diskord.ext.commands.CommandNotFound
    :members:

.. autoexception:: diskord.ext.commands.DisabledCommand
    :members:

.. autoexception:: diskord.ext.commands.CommandInvokeError
    :members:

.. autoexception:: diskord.ext.commands.TooManyArguments
    :members:

.. autoexception:: diskord.ext.commands.UserInputError
    :members:

.. autoexception:: diskord.ext.commands.CommandOnCooldown
    :members:

.. autoexception:: diskord.ext.commands.MaxConcurrencyReached
    :members:

.. autoexception:: diskord.ext.commands.NotOwner
    :members:

.. autoexception:: diskord.ext.commands.MessageNotFound
    :members:

.. autoexception:: diskord.ext.commands.MemberNotFound
    :members:

.. autoexception:: diskord.ext.commands.GuildNotFound
    :members:

.. autoexception:: diskord.ext.commands.UserNotFound
    :members:

.. autoexception:: diskord.ext.commands.ChannelNotFound
    :members:

.. autoexception:: diskord.ext.commands.ChannelNotReadable
    :members:

.. autoexception:: diskord.ext.commands.ThreadNotFound
    :members:

.. autoexception:: diskord.ext.commands.BadColourArgument
    :members:

.. autoexception:: diskord.ext.commands.RoleNotFound
    :members:

.. autoexception:: diskord.ext.commands.BadInviteArgument
    :members:

.. autoexception:: diskord.ext.commands.EmojiNotFound
    :members:

.. autoexception:: diskord.ext.commands.PartialEmojiConversionFailure
    :members:

.. autoexception:: diskord.ext.commands.GuildStickerNotFound
    :members:

.. autoexception:: diskord.ext.commands.BadBoolArgument
    :members:

.. autoexception:: diskord.ext.commands.MissingPermissions
    :members:

.. autoexception:: diskord.ext.commands.BotMissingPermissions
    :members:

.. autoexception:: diskord.ext.commands.MissingRole
    :members:

.. autoexception:: diskord.ext.commands.BotMissingRole
    :members:

.. autoexception:: diskord.ext.commands.MissingAnyRole
    :members:

.. autoexception:: diskord.ext.commands.BotMissingAnyRole
    :members:

.. autoexception:: diskord.ext.commands.NSFWChannelRequired
    :members:

.. autoexception:: diskord.ext.commands.FlagError
    :members:

.. autoexception:: diskord.ext.commands.BadFlagArgument
    :members:

.. autoexception:: diskord.ext.commands.MissingFlagArgument
    :members:

.. autoexception:: diskord.ext.commands.TooManyFlags
    :members:

.. autoexception:: diskord.ext.commands.MissingRequiredFlag
    :members:

.. autoexception:: diskord.ext.commands.ExtensionError
    :members:

.. autoexception:: diskord.ext.commands.ExtensionAlreadyLoaded
    :members:

.. autoexception:: diskord.ext.commands.ExtensionNotLoaded
    :members:

.. autoexception:: diskord.ext.commands.NoEntryPointError
    :members:

.. autoexception:: diskord.ext.commands.ExtensionFailed
    :members:

.. autoexception:: diskord.ext.commands.ExtensionNotFound
    :members:

.. autoexception:: diskord.ext.commands.CommandRegistrationError
    :members:


Exception Hierarchy
~~~~~~~~~~~~~~~~~~~~~

.. exception_hierarchy::

    - :exc:`~.DiscordException`
        - :exc:`~.commands.CommandError`
            - :exc:`~.commands.ConversionError`
            - :exc:`~.commands.UserInputError`
                - :exc:`~.commands.MissingRequiredArgument`
                - :exc:`~.commands.TooManyArguments`
                - :exc:`~.commands.BadArgument`
                    - :exc:`~.commands.MessageNotFound`
                    - :exc:`~.commands.MemberNotFound`
                    - :exc:`~.commands.GuildNotFound`
                    - :exc:`~.commands.UserNotFound`
                    - :exc:`~.commands.ChannelNotFound`
                    - :exc:`~.commands.ChannelNotReadable`
                    - :exc:`~.commands.BadColourArgument`
                    - :exc:`~.commands.RoleNotFound`
                    - :exc:`~.commands.BadInviteArgument`
                    - :exc:`~.commands.EmojiNotFound`
                    - :exc:`~.commands.GuildStickerNotFound`
                    - :exc:`~.commands.PartialEmojiConversionFailure`
                    - :exc:`~.commands.BadBoolArgument`
                    - :exc:`~.commands.ThreadNotFound`
                    - :exc:`~.commands.FlagError`
                        - :exc:`~.commands.BadFlagArgument`
                        - :exc:`~.commands.MissingFlagArgument`
                        - :exc:`~.commands.TooManyFlags`
                        - :exc:`~.commands.MissingRequiredFlag`
                - :exc:`~.commands.BadUnionArgument`
                - :exc:`~.commands.BadLiteralArgument`
                - :exc:`~.commands.ArgumentParsingError`
                    - :exc:`~.commands.UnexpectedQuoteError`
                    - :exc:`~.commands.InvalidEndOfQuotedStringError`
                    - :exc:`~.commands.ExpectedClosingQuoteError`
            - :exc:`~.commands.CommandNotFound`
            - :exc:`~.commands.CheckFailure`
                - :exc:`~.commands.CheckAnyFailure`
                - :exc:`~.commands.PrivateMessageOnly`
                - :exc:`~.commands.NoPrivateMessage`
                - :exc:`~.commands.NotOwner`
                - :exc:`~.commands.MissingPermissions`
                - :exc:`~.commands.BotMissingPermissions`
                - :exc:`~.commands.MissingRole`
                - :exc:`~.commands.BotMissingRole`
                - :exc:`~.commands.MissingAnyRole`
                - :exc:`~.commands.BotMissingAnyRole`
                - :exc:`~.commands.NSFWChannelRequired`
            - :exc:`~.commands.DisabledCommand`
            - :exc:`~.commands.CommandInvokeError`
            - :exc:`~.commands.CommandOnCooldown`
            - :exc:`~.commands.MaxConcurrencyReached`
        - :exc:`~.commands.ExtensionError`
            - :exc:`~.commands.ExtensionAlreadyLoaded`
            - :exc:`~.commands.ExtensionNotLoaded`
            - :exc:`~.commands.NoEntryPointError`
            - :exc:`~.commands.ExtensionFailed`
            - :exc:`~.commands.ExtensionNotFound`
    - :exc:`~.ClientException`
        - :exc:`~.commands.CommandRegistrationError`
