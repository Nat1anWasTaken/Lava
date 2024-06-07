from logging import getLogger

from disnake import InteractionResponded, ApplicationCommandInteraction, \
    MessageInteraction
from disnake.ext import commands
from disnake.ext.commands import Cog, CommandInvokeError
from lavalink import TrackEndEvent, TrackLoadFailedEvent, QueueEndEvent, TrackStartEvent, PlayerUpdateEvent

from lava.bot import Bot
from lava.classes.player import LavaPlayer
from lava.embeds import ErrorEmbed
from lava.errors import MissingVoicePermissions, BotNotInVoice, UserNotInVoice, UserInDifferentChannel
from lava.utils import ensure_voice


class Events(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.logger = getLogger("lava.events")

    async def cog_load(self):
        await self.bot.wait_until_ready()

    @Cog.listener(name="on_ready")
    async def on_ready(self):
        self.bot.lavalink.add_event_hook(self.on_player_update, event=PlayerUpdateEvent)
        self.bot.lavalink.add_event_hook(self.on_track_start, event=TrackStartEvent)
        self.bot.lavalink.add_event_hook(self.on_track_end, event=TrackEndEvent)
        self.bot.lavalink.add_event_hook(self.on_queue_end, event=QueueEndEvent)
        self.bot.lavalink.add_event_hook(self.on_track_load_failed, event=TrackLoadFailedEvent)

    async def on_player_update(self, event: PlayerUpdateEvent):
        player: LavaPlayer = event.player

        self.bot.logger.info("Received player update event for guild %s", player.guild)

        try:
            await player.update_display()
        except ValueError:
            pass

    async def on_track_start(self, event: TrackStartEvent):
        player: LavaPlayer = event.player

        self.bot.logger.info("Received track start event for guild %s", player.guild)

        player._lyrics = None  # Reset the lyrics cache

        try:
            await player.update_display()
        except ValueError:
            pass

    async def on_track_end(self, event: TrackEndEvent):
        player: LavaPlayer = event.player

        self.bot.logger.info("Received track end event for guild %s", player.guild)

        try:
            await player.update_display()
        except ValueError:
            pass

    async def on_queue_end(self, event: QueueEndEvent):
        player: LavaPlayer = event.player

        self.bot.logger.info("Received queue end event for guild %s", player.guild)

        await player.guild.voice_client.disconnect(force=False)

        try:
            await player.update_display()
        except ValueError:
            pass

    async def on_track_load_failed(self, event: TrackLoadFailedEvent):
        player: LavaPlayer = event.player

        self.bot.logger.info("Received track load failed event for guild %s", player.guild)

        message = await player.message.channel.send(
            embed=ErrorEmbed(
                f"{player.bot.get_text('error.play_failed', player.locale, '無法播放歌曲')}: {event.track['title']}",
                f"{player.bot.get_text('reason', player.locale, '原因')}: `{event.original or 'Unknown'}`"
            )
        )
        await player.skip()
        await player.update_display(message, delay=5)

    @commands.Cog.listener(name="on_slash_command_error")
    async def on_slash_command_error(self, interaction: ApplicationCommandInteraction, error: CommandInvokeError):
        if isinstance(error.original, MissingVoicePermissions):
            embed = ErrorEmbed(
                self.bot.get_text('error.command.title', interaction.locale, '指令錯誤'),
                self.bot.get_text(
                    'error.no_play_perms', interaction.locale, "我需要 `連接` 和 `說話` 權限才能夠播放音樂"
                )
            )

        elif isinstance(error.original, BotNotInVoice):
            embed = ErrorEmbed(
                self.bot.get_text('error.command.title', interaction.locale, '指令錯誤'),
                self.bot.get_text('error.bot_not_in_voice', interaction.locale, "我沒有連接到一個語音頻道")
            )

        elif isinstance(error.original, UserNotInVoice):
            embed = ErrorEmbed(
                self.bot.get_text('error.command.title', interaction.locale, '指令錯誤'),
                self.bot.get_text('error.user_not_in_voice', interaction.locale, "你沒有連接到一個語音頻道")
            )

        elif isinstance(error.original, UserInDifferentChannel):
            embed = ErrorEmbed(
                self.bot.get_text('error.command.title', interaction.locale, '指令錯誤'),
                f"{self.bot.get_text('error.must_in_same_voice', interaction.locale, '你必須與我在同一個語音頻道')} <#{error.original.voice.id}>"
            )

        else:
            raise error.original

        try:
            await interaction.response.send_message(embed=embed)
        except InteractionResponded:
            await interaction.edit_original_response(embed=embed)

    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update(self, member, before, after):
        if (
                before.channel is not None
                and after.channel is None
                and member.id == self.bot.user.id
        ):
            player = self.bot.lavalink.player_manager.get(member.guild.id)

            if player is not None:
                await player.stop()
                player.queue.clear()

                try:
                    await player.update_display()
                except ValueError:  # There's no message to update
                    pass

    @commands.Cog.listener(name="on_message_interaction")
    async def on_message_interaction(self, interaction: MessageInteraction):
        if interaction.data.custom_id.startswith("control"):
            if interaction.data.custom_id.startswith("control.empty"):
                await interaction.response.edit_message()

                return

            try:
                await ensure_voice(interaction, should_connect=False)
            except (UserNotInVoice, BotNotInVoice, MissingVoicePermissions, UserInDifferentChannel):
                return

            player = self.bot.lavalink.player_manager.get(interaction.guild_id)

            match interaction.data.custom_id:
                case "control.resume":
                    await player.set_pause(False)

                case "control.pause":
                    await player.set_pause(True)

                case "control.stop":
                    await player.stop()
                    player.queue.clear()
                    await interaction.guild.voice_client.disconnect(force=False)

                case "control.previous":
                    await player.seek(0)

                case "control.next":
                    await player.skip()

                case "control.shuffle":
                    player.set_shuffle(not player.shuffle)

                case "control.repeat":
                    player.set_loop(player.loop + 1 if player.loop < 2 else 0)

                case "control.rewind":
                    await player.seek(round(player.position) - 10000)

                case "control.forward":
                    await player.seek(round(player.position) + 10000)

                case "control.autoplay":
                    await player.toggle_autoplay()

                case "control.lyrics":
                    await player.toggle_lyrics()

            await player.update_display(interaction=interaction)


def setup(bot):
    bot.add_cog(Events(bot))
