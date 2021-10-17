"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Discord API.

:copyright: (c) 2015-present Rapptz
:license: MIT, see LICENSE for more details.

"""

__title__ = "discord"
__author__ = "Rapptz"
__license__ = "MIT"
__copyright__ = "Copyright 2015-present Rapptz"
__version__ = "2.6.0a"

__path__ = __import__("pkgutil").extend_path(__path__, __name__)

import logging
from typing import NamedTuple, Literal

from .activity import *
from .appinfo import *
from .application_commands import *
from .asset import *
from .colour import *
from .components import *
from .client import *
from .emoji import *
from .errors import *
from .file import *
from .flags import *
from .guild import *
from .user import *
from .partial_emoji import *
from .channel import *
from .member import *
from .message import *
from .permissions import *
from .role import *
from .integrations import *
from .invite import *
from .template import *
from .widget import *
from .object import *
from .reaction import *
from .enums import *
from .embeds import *
from .mentions import *
from .shard import *
from .player import *
from .webhook import *
from .voice_client import *
from .audit_logs import *
from .raw_models import *
from .team import *
from .sticker import *
from .stage_instance import *
from .interactions import *
from .threads import *
from .welcome_screen import *
from . import utils, opus, abc, ui, application


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int


version_info: VersionInfo = VersionInfo(
    major=2, minor=5, micro=0, releaselevel="alpha", serial=0
)

logging.getLogger(__name__).addHandler(logging.NullHandler())
