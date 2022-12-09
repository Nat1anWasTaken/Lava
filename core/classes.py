from disnake.ext.commands import Bot as OriginalBot
from lavalink import Client


class Bot(OriginalBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.lavalink = Client(user_id=self.user.id)
