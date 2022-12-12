import json

from disnake.abc import MISSING
from disnake.ext.commands import Bot as OriginalBot
from lavalink import Client


class Bot(OriginalBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.lavalink: Client = MISSING
        self.icons: dict = MISSING

    def assign_lavalink_client(self, client: Client):
        """
        Assigns a Lavalink client to the bot.
        This must be called before any other Lavalink-related code is executed.
        """
        self.lavalink: Client = client

    def load_icons(self, file_path: str):
        """
        Load icons from a json file
        :param file_path: The path to the json file
        """
        with open(file_path, "r") as f:
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
