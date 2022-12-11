from disnake.abc import MISSING
from disnake.ext.commands import Bot as OriginalBot
from lavalink import Client


class Bot(OriginalBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.lavalink: Client = MISSING

    def assign_lavalink_client(self, client: Client):
        """
        Assigns a Lavalink client to the bot.
        This must be called before any other Lavalink-related code is executed.
        """
        self.lavalink: Client = client
