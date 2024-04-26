from lavalink import Client

from lava.bot import Bot
from lava.classes.player import LavaPlayer
from lava.classes.player_manager import LavaPlayerManager


class LavalinkClient(Client):
    def __init__(self, bot: "Bot", *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bot: Bot = bot
        self.player_manager = LavaPlayerManager(bot=bot, client=self, player=LavaPlayer)
