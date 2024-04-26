import json
from logging import Logger
from typing import Optional

from disnake import Locale
from disnake.ext.commands import Bot as OriginalBot

from lava.lavalink.lavalink_client import LavalinkClient
from lava.source import SourceManager


class Bot(OriginalBot):
    def __init__(self, logger: Logger, **kwargs):
        super().__init__(**kwargs)

        self.logger = logger

        self._lavalink: Optional[LavalinkClient] = None

        with open("configs/icons.json", "r", encoding="utf-8") as f:
            self.icons = json.load(f)

    async def on_ready(self):
        self.logger.info("The bot is ready! Logged in as %s" % self.user)

        self.__setup_lavalink_client()

    @property
    def lavalink(self) -> LavalinkClient:
        if not self.is_ready():
            raise RuntimeError("The bot is not ready yet!")

        if self._lavalink is None:
            self.__setup_lavalink_client()

        return self._lavalink

    def __setup_lavalink_client(self):
        """
        Sets up the lavalink client for the bot
        :return: Lavalink Client
        """
        self.logger.info("Setting up lavalink client...")

        self._lavalink = LavalinkClient(self, user_id=self.user.id)

        self.logger.info("Loading lavalink nodes...")

        with open("configs/lavalink.json", "r") as f:
            config = json.load(f)

        for node in config['nodes']:
            self.logger.debug("Adding lavalink node %s", node['host'])

            self.lavalink.add_node(**node)

        self.logger.info("Done loading lavalink nodes!")

        self.lavalink.register_source(SourceManager())

    def get_text(self, key: str, locale: Locale, default: str = None) -> str:
        """
        Gets a text from i18n files by key
        :param key: The key of the text
        :param locale: The locale of the text
        :param default: The default value to return if the text is not found
        :return: The text
        """
        return self.i18n.get(key).get(str(locale), default)

    def get_icon(self, name: str, default: any) -> any:
        """
        Get an icon
        :param name: The name of the icon
        :param default: The default value to return if the icon is not found
        :return: The icon
        """
        dct = self.icons.copy()

        for key in name.split("."):
            try:
                dct = dct[key]
            except KeyError:
                return default

        return dct
