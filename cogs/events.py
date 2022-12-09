from disnake.ext.commands import Cog
from lavalink import QueueEndEvent


class Events(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.lavalink.add_event_hook(self.track_hook)

    async def track_hook(self, event):
        if isinstance(event, QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voicechannel.
            guild_id = event.player.guild_id
            guild = self.bot.get_guild(guild_id)
            await guild.voice_client.disconnect(force=True)


def setup(bot):
    bot.add_cog(Events(bot))
