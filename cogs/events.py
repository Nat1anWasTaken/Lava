import logging
from typing import Union

import lavalink
from disnake import TextChannel, Thread, Message, VoiceProtocol
from disnake.abc import GuildChannel
from disnake.ext import commands
from disnake.ext.commands import Cog
from disnake.utils import get
from lavalink import QueueEndEvent, TrackLoadFailedEvent, DefaultPlayer, TrackStartEvent

from core.classes import Bot
from core.embeds import ErrorEmbed
from library.classes import LavalinkVoiceClient
from library.errors import MissingVoicePermissions, BotNotInVoice, UserNotInVoice, UserInDifferentChannel
from library.functions import update_display


class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        lavalink.add_event_hook(self.track_hook)

    async def track_hook(self, event):
        if isinstance(event, QueueEndEvent):
            # When this track_hook receives a "QueueEndEvent" from lavalink.py
            # it indicates that there are no tracks left in the player's queue.
            # To save on resources, we can tell the bot to disconnect from the voice channel.
            guild_id = event.player.guild_id

            guild = self.bot.get_guild(guild_id)

            try:
                await guild.voice_client.disconnect(force=True)
            except AttributeError:
                pass

        elif isinstance(event, TrackLoadFailedEvent):
            player: DefaultPlayer = event.player

            # noinspection PyTypeChecker
            channel: Union[GuildChannel, TextChannel, Thread] = self.bot.get_channel(int(player.fetch("channel")))

            # noinspection PyTypeChecker
            message: Message = await channel.fetch_message(int(player.fetch("message")))

            await channel.send(
                embed=ErrorEmbed(f"無法播放歌曲: {event.track.data['title']}"),
                reference=message
            )

            player.store("message", message.id)

        elif isinstance(event, TrackStartEvent):
            player: DefaultPlayer = event.player

            try:
                await update_display(self.bot, player)
            except ValueError:
                pass

    @commands.Cog.listener(name="on_slash_command_error")
    async def on_slash_command_error(self, interaction, error):
        if isinstance(error.original, MissingVoicePermissions):
            await interaction.response.send_message(
                embed=ErrorEmbed("指令錯誤", "我需要 `連接` 和 `說話` 權限才能夠播放音樂")
            )

        elif isinstance(error.original, BotNotInVoice):
            await interaction.response.send_message(
                embed=ErrorEmbed("指令錯誤", "我沒有連接到一個語音頻道")
            )

        elif isinstance(error.original, UserNotInVoice):
            await interaction.response.send_message(
                embed=ErrorEmbed("指令錯誤", "你沒有連接到一個語音頻道")
            )

        elif isinstance(error.original, UserInDifferentChannel):
            await interaction.response.send_message(
                embed=ErrorEmbed("指令錯誤", f"你必須與我在同一個語音頻道 <#{error.original.voice.id}>")
            )

        else:
            raise error.original

    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None and after.channel is None:  # This means the user left the voice channel
            if member.id == self.bot.user.id:
                player: DefaultPlayer = self.bot.lavalink.player_manager.get(member.guild.id)

                try:
                    await update_display(self.bot, player)
                except ValueError:  # There's no message to update
                    pass

                self.bot.lavalink.player_manager.remove(member.guild.id)


def setup(bot):
    bot.add_cog(Events(bot))
