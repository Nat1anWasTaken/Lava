import json

from disnake.abc import MISSING
from disnake.ext.commands import Bot as OriginalBot
from lavalink import Client

from library.sources.source import SourceManager


class Bot(OriginalBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.lavalink: Client = MISSING

        self.icons: dict = MISSING

    async def on_ready(self):
        self.__setup_lavalink_client()
        self.__load_icons()

    def __setup_lavalink_client(self):
        """
        Sets up the lavalink client for the bot
        :return: Lavalink Client
        """
        self.lavalink = Client(self.user.id)

        with open("configs/lavalink.json", "r") as f:
            config = json.load(f)

        for node in config['nodes']:
            self.lavalink.add_node(**node)

        self.lavalink.register_source(SourceManager())

    def __load_icons(self):
        """
        Load icons from a json file
        """
        with open("configs/icons.json", "r") as f:
            self.icons = json.load(f)

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
