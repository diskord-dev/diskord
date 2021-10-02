.. currentmodule:: diskord

.. _migrating_2_0:

Migrating to v2.x
=================

v2.0 is the latest major and breaking release of this library. This version not only brings
the long-awaited new API features like interactions, threads etc. but also brings many breaking 
changes that can affect all the bots updating to v2 from v1.x.

This migration guide covers the prominent additions, bug fixes and most importantly breaking
changes to help you easily migrate to v2. We highly suggest you reading this guide to avoid
running into unexpected issues.

Python requirement
------------------

Prior v2, In v1.x, The minimum Python version required was 3.5, This is not the case in v2.
To make development easier and allow our dependencies to adapt new versions, Support for Python version
lower then 3.8 has been dropped.

You now need *Python 3.8 or higher* to use this library.

Removal of Non-bot accounts support
-----------------------------------

v2.0 removes all the previously depreciated user endpoints. Please note that userbots are
against Discord ToS. This library will not provide coverage to such things that are against
ToS.

This includes the following methods and attributes:

* ``Bot.fetch_user_profile()``
* ``ClientUser.unblock()``
* ``ClientUser.relationships``
* ``ClientUser.friends``
* ``ClientUser.create_group()``
* ``ClientUser.edit_settings()``
* ``User.relationships``
* ``User.mutual_friends()``
* ``User.is_friend()``
* ``User.is_blocked()``
* ``User.block()``
* ``User.unblock()``
* ``User.remove_friend()``
* ``User.send_friend_request()``
* ``User.profile()``
* ``Member.relationships``
* ``Member.mutual_friends()``
* ``Member.is_friend()``
* ``Member.is_blocked()``
* ``Member.block()``
* ``Member.unblock()``
* ``Member.remove_friend()``
* ``Member.send_friend_request()``
* ``Member.profile()``
* The ``afk`` parameter from :meth:`Client.change_presence`
* Events: ``on_relationship_add`` and ``on_relationship_update``
* Classes: ``Profile``, ``Relationship``, ``CallMessage``, ``GroupCall``


Removals and Deprecations
-------------------------

Certain methods, attributes or parameters etc. have been removed or deprecated in v2.0 in
favor of some other methods. The below table comprehensively lists some removed things with
reasons and the methods to be replaced with:

+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
|         Deprecated                                           |        In favor of                        |        Extra info (if any)        |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
|        ``Client.logout()``                                   |   :meth:`Client.close()`                  |                 -                 |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``Guild/Client.request_offline_members``                     |   :meth:`Guild.chunk()`                   |                 -                 |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``ExtensionNotFound.original``                               |      none (See info)                      |  Had no use and was unnecessary.  |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``on_private_channel_create``, ``on_private_channel_delete`` |      none (See info)                      |  Bots no longer get these events. |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``commands.HelpCommand.clean_prefix``                        | :attr:`~commands.Context.clean_prefix`    |                 -                 |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``fetch_offline_members`` parameter in :class:`Client`       | :attr:`Client.chunk_guilds_at_startup`    |  Was deprecated since v1.5.       |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``User.permissions_in``, ``Member.permissions_in``           | :meth:`abc.GuildChannel.permissions_for`  |                 -                 |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``Sticker.preview_image``                                    |      none (See info)                      | Discord no longer provides this.  |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``commands.Bot.self_bot``                                    |      none (See info)                      | Userbots are no longer supported  |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+
| ``Sticker.tags``                                             |  :attr:`StandardSticker.tags`             |                 -                 |
+--------------------------------------------------------------+-------------------------------------------+-----------------------------------+


Renaming and fixes
------------------

Certain things are renamed and fixed in v2.x, Here's a list:

* ``commands.MissingPermissions.missing_perms`` -> :attr:`~ext.commands.MissingPermissions.missing_permissions`
* ``Color.blurple`` -> ``Color.og_blurple`` [*]
* ``StickerType``, an enum of sticker formats, is renamed to :class:`StickerFormatType`. [**]
* ``Reaction.custom_emoji`` property -> :meth:`Reaction.is_custom_emoji` method.
* :attr:`Message.type` for replies are now :attr:`MessageType.reply`
* All getters and fetchers methods now take arguments as positional-only. 
i.e ``Client.get_member(id=...)`` is no longer supported, you must specify id as positional argument. i.e ``Client.get_member(id)``
* :attr:`IntegrationAccount.id` is now :class:`str`, instead of :class:`int`, due to Discord changes.



[*] :meth:`Color.blurple` returns the new blurple color whereas :meth:`Color.og_blurple` returns
old one.

[**]  Old name is used for a new enum with different purpose (checking if the sticker is guild sticker or Nitro sticker)

Webhook Types Split
-------------------

Previously, Webhook had one class ``Webhook`` for both asynchronous and synchronous operations.
In v2.x, This has been splitted to :class:`Webhook` and :class:`SyncWebhook` for async and
sync operations respectively.

Before: ::
    
    from diskord import Webhook, RequestsWebhookAdapter, AsyncWebhookAdapter

    webhook = Webhook.from_url('url-here', adapter=RequestsWebhookAdapter()) # for sync
    webhook = Webhook.from_url('url-here', adapter=AsyncWebhookAdapter(session)) # for async

Now: ::
    
    from diskord import Webhook, SyncWebhook
    import aiohttp
    
    async with aiohttp.ClientSession() as session: # async
        webhook = Webhook.partial(
            id,
            token,
            session=session
        )
        await webhook.send("Hello world.")

    webhook = SyncWebhook.from_url('url-here') # for sync 


* :class:`Webhook` and :class:`WebhookMessage` are now always asynchronouns. For synchronouns use (requests), use :class:`SyncWebhook` and :class:`SyncWebhookMessage`.
* :class:`WebhookAdapter`, :class:`AsyncWebhookAdapter`, and :class:`RequestsWebhookAdapter` are removed, since they are unnecessary.
* ``adapter`` arguments of :meth:`Webhook.partial` and :meth:`Webhook.from_url` are removed. Sessions are now passed directly to partial/from_url.

Assets Redesign
---------------

Assets have been completely redesigned in v2.x.

* Asset-related attributes that previously returned hash strings (e.g. ``User.avatar``) now returns ``Asset``. ``Asset.key`` returns the hash from now on.
* ``Class.x_url`` and ``Class.x_url_as`` are removed. :meth:`Asset.replace` or :meth:`Asset.with_x` methods can be used to get specific asset sizes or types.
* :attr:`Emoji.url` and :attr:`PartialEmoji.url` are now :class:`str`. :meth:`Emoji.save` and :meth:`Emoji.read` are added to save or read emojis.
* ``Emoji.url_as`` and ``PartialEmoji.url_as`` are removed.
* Some :class:`AuditLogDiff` attributes now return :class:`Asset` instead of :class:`str`: ``splash``, ``icon``, ``avatar``
* :attr:`User.avatar` returns ``None`` if the avatar is not set and is instead the default avatar; use :attr:`User.display_avatar` for pre-2.0 behavior. 
* Attributes that returned Asset are renamed, e.g. attributes ending with ``_url`` (i.e. ``avatar_url``) are changed to ``avatar.url``. ``User.avatar`` returns None in case the default avatar is used.

Use of timezone aware time
--------------------------

TL;DR: ``utcnow`` becomes ``now(datetime.timezone.utc)``. If you are constructing ``datetime`` yourself,
pass ``tzinfo=datetime.timezone.utc``.

Example: ::
    
    embed = diskord.Embed(
        title = "Embed with timestamp",
        timestamp = datetime(2021, 3, 14, 15, 9, 2, tzinfo=timezone.utc)
    )

    # or

    embed = diskord.Embed(
        title='Embed with timestamp',
        timestamp=diskord.utils.utcnow()
    )

Note that newly-added :func:`utils.utcnow()` can be used as a short-hand of ``datetime.datetime.now(datetime.timezone.utc)``.


Edit Behaviour Changes
----------------------

``edit`` methods of most classes no longer update the cache in-place, and instead returns the 
modified instance.

:func:`on_socket_raw_receive` behavior
--------------------------------------

``on_socket_raw_receive`` is no longer dispatched for incomplete data, and the value passed is 
always decompressed and decoded to :class:`str`. Previously, when received a multi-part 
zlib-compressed binary message, :func:`on_socket_raw_receive` was dispatched on all messages 
with the compressed, encoded bytes.

Context attributes
------------------

The following :class:`~ext.commands.Context` attributes can now be ``None``: 
* prefix 
* command
* invoked_with
* invoked_subcommand. 

Threads Support
---------------

Thread support was added in v2.0 and with this addition, There're some breaking changes.

TL;DR: Most Methods and attributes that returned :class:`TextChannel`, etc can now return :class:`Thread`.

* :meth:`Client.get_channel` can now return :class:`Thread`.
* :meth:`Client.fetch_channel` and :meth:`Guild.fetch_channel` can now return :class:`Thread`.
* :attr:`ext.commands.NSFWChannelRequired.channel` can now return :class:`Thread`.
* :attr:`ext.commands.ChannelNotReadable.argument` can now return :class:`Thread`.
* :attr:`Message.channel` can now return :class:`Thread`.

Splitting up of status activity listeners
-----------------------------------------

:func:`on_member_update` event is no longer dispatched for status/activity changes. 
Use :func:`on_presence_update` instead.

Additions
---------

These are not breaking changes but few major additions in v2.x.

* Threads support
* Application Commands i.e Slash commands, Context menu commands etc.
* Partial support for application command extensions i.e Checks, Converters
* Full Stickers Support
* Message Components and interactions
* Stage instances support
* Guild Welcome Screens
* User banners support
* Removal helpers for embeds
* Integration create/delete/edit events.
* Support for editing guild widgets
* Support for bot integrations
* Invite targets for voice channel invites
* Color class can now be typecasted to :class:`int`
* Add Discord Certified Moderator user flag
* Add support for explicit time parameter in ext.tasks.
* Add :class:`fetch_message` to webhooks.
* Add :class:`ApplicationFlags`
* Add :class:`~commands.GuildChannelConverter`.
* Add :class:`~commands.ObjectConverter`
* Add :meth:`Client.fetch_invite`
* Add :meth:`Color.fuchsia` & :meth:`Color.yellow`
* Add :meth:`Role.is_assignable`
* Add :meth:`Member.get_role`
* Add :meth:`Guild.delete_custom_emoji` method
* Add :func:`on_raw_typing` event for DM typing.
* Add :attr:`Template.url`
* Add :attr:`ext.Command.extras` to attach additional data to command.
* Add :attr:`Activity.buttons`
* Add :meth:`Template.is_dirty`
* Add :attr:`VoiceChannel.video_quality_mode`

There are many other minor changes that're not listed here.