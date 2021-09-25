:orphan:

.. _discord-intro:
.. currentmodule:: diskord
.. versionadded:: 2.0

Migrating to v2.x
=================

v2.0 is the latest major and breaking release of this library. This version not only brings
the long-awaited new API features but also brings many breaking changes that can affect
all the bots updating to v2 from v1.x.

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

Removals and Deprecations
-------------------------

Certain methods, attributes or parameters etc. have been removed or deprecated in v2.0 in
favor of some other methods. The below table comprehensively lists some removed things with
reasons and the methods to be replaced with:

+--------------------------------------------------------------+----------------------------------------+-----------------------------------+
|         Deprecated                                           |        In favor of                     |        Extra info (if any)        |
+--------------------------------------------------------------+----------------------------------------+-----------------------------------+
|        ``Client.logout()``                                   |   :meth:`Client.close()`               |                 -                 |
+--------------------------------------------------------------+----------------------------------------+-----------------------------------+
| ``Guild.request_offline_members``                            |   :meth:`Guild.chunk()`                |                 -                 |
+--------------------------------------------------------------+----------------------------------------+-----------------------------------+
| ``ExtensionNotFound.original``                               |      none (See info)                   |  Had no use and was unnecessary.  |
+--------------------------------------------------------------+----------------------------------------+-----------------------------------+
| ``on_private_channel_create``, ``on_private_channel_delete`` |      none (See info)                   |  Bots no longer get these events. |
+--------------------------------------------------------------+----------------------------------------+-----------------------------------+
| ``commands.HelpCommand.clean_prefix``                        | :attr:`commands.Context.clean_prefix`  |                 -                 |
+--------------------------------------------------------------+----------------------------------------+-----------------------------------+
| ``fetch_offline_members`` parameter in :class:`Client`       | :attr:`Client.chunk_guilds_at_startup` |  Was deprecated since v1.5.       |
+--------------------------------------------------------------+----------------------------------------+-----------------------------------+


