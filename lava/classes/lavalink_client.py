from typing import TYPE_CHECKING

from lavalink import Client

from lava.classes.player import LavaPlayer
from lava.classes.player_manager import LavaPlayerManager

if TYPE_CHECKING:
    from lava.bot import Bot


class LavalinkClient(Client):
    def __init__(self, bot: "Bot", *args, **kwargs):
        super().__init__(player=LavaPlayer, *args, **kwargs)

        self.bot: Bot = bot
        self.player_manager: LavaPlayerManager = LavaPlayerManager(bot=bot, client=self)
