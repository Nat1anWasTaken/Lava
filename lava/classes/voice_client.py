from typing import TYPE_CHECKING

from disnake import VoiceClient, VoiceChannel
from disnake.utils import get

if TYPE_CHECKING:
    from lava.bot import Bot
    from lava.classes.lavalink_client import LavalinkClient


class LavalinkVoiceClient(VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, bot: "Bot", channel: VoiceChannel):
        self.bot = bot
        self.channel = channel
        self.lavalink: "LavalinkClient" = bot.lavalink
        super().__init__(bot, channel)

    async def on_voice_server_update(self, data):
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.bot.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }

        if data['channel_id']:
            channel = get(self.channel.guild.voice_channels, id=int(data['channel_id']))
            self.channel = channel
            await self.lavalink.voice_update_handler(lavalink_data)
        else:
            await self.channel.guild.change_voice_state(channel=None)
            self.cleanup()

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False,
                      self_mute: bool = False) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        self.lavalink.player_manager.new(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player = self.lavalink.player_manager.get(self.channel.guild.id)

        if not force and not player.is_connected:
            return

        await self.channel.guild.change_voice_state(channel=None)

        await player.stop()
        await player.update_display()

        await player.destroy()

        self.cleanup()
