import asyncio
from asyncio import Task
from time import time
from typing import TYPE_CHECKING, Optional, Union

from disnake import Message, Locale, ButtonStyle, Embed, Colour, Guild, Interaction
from disnake.ui import ActionRow, Button
from lavalink import DefaultPlayer, Node, parse_time

from lava.embeds import ErrorEmbed
from lava.utils import get_recommended_tracks, get_image_size

if TYPE_CHECKING:
    from lava.bot import Bot


class LavaPlayer(DefaultPlayer):
    def __init__(self, bot: "Bot", guild_id: int, node: Node):
        super().__init__(guild_id, node)

        self.bot: Bot = bot
        self.message: Optional[Message] = None
        self.locale: Locale = Locale.zh_TW

        self._guild: Optional[Guild] = None

        self.autoplay: bool = False

        self._last_update: int = 0
        self._last_position = 0
        self.position_timestamp = 0

        self.__display_image_as_wide: Optional[bool] = None
        self.__last_image_url: str = ""

        self.timeout_task: Optional[Task] = None

    @property
    def guild(self) -> Optional[Guild]:
        if not self._guild:
            self._guild = self.bot.get_guild(self.guild_id)

        return self._guild

    async def check_autoplay(self) -> bool:
        """
        Check the autoplay status and add recommended tracks if enabled.

        :return: True if tracks were added, False otherwise.
        """
        if not self.autoplay or len(self.queue) >= 5:
            return False
        self.bot.logger.info(
            "Queue is empty, adding recommended track for guild %s...", self.guild
        )

        recommendations = await get_recommended_tracks(self, self.current, 5 - len(self.queue))

        for recommendation in recommendations:
            self.add(requester=0, track=recommendation)

    async def toggle_autoplay(self):
        """
        Toggle autoplay for the player.
        """
        if not self.autoplay:
            self.autoplay = True
            return

        self.autoplay = False

        for item in self.queue:  # Remove songs added by autoplay
            if item.requester == 0:
                self.queue.remove(item)

    async def update_display(self,
                             new_message: Optional[Message] = None,
                             delay: int = 0,
                             interaction: Optional[Interaction] = None,
                             locale: Optional[Locale] = None) -> None:
        """
        Update the display of the current song.

        Note: If new message is provided, Old message will be deleted after 5 seconds

        :param new_message: The new message to update the display with, None to use the old message.
        :param delay: The delay in seconds before updating the display.
        :param interaction: The interaction to be responded to.
        :param locale: The locale to use for the display
        """
        if interaction:
            self.locale = interaction.locale

        if locale:
            self.locale = locale

        self.bot.logger.info(
            "Updating display for player in guild %s in a %s seconds delay", self.bot.get_guild(self.guild_id), delay
        )

        await asyncio.sleep(delay)

        if not self.message and not new_message:
            self.bot.logger.warning(
                "No message to update display for player in guild %s", self.bot.get_guild(self.guild_id)
            )
            return

        if new_message:
            try:
                self.bot.logger.debug(
                    "Deleting old existing display message for player in guild %s", self.bot.get_guild(self.guild_id)
                )

                _ = self.bot.loop.create_task(self.message.delete())
            except (AttributeError, UnboundLocalError):
                pass

            self.message = new_message

        if not self.is_connected or not self.current:
            components = []

        else:
            components = [
                ActionRow(
                    Button(
                        style=ButtonStyle.green if self.shuffle else ButtonStyle.grey,
                        emoji=self.bot.get_icon('control.shuffle', "🔀"),
                        custom_id="control.shuffle"
                    ),
                    Button(
                        style=ButtonStyle.blurple,
                        emoji=self.bot.get_icon('control.previous', "⏮️"),
                        custom_id="control.previous"
                    ),
                    Button(
                        style=ButtonStyle.green,
                        emoji=self.bot.get_icon('control.pause', "⏸️"),
                        custom_id="control.pause"
                    ) if not self.paused else Button(
                        style=ButtonStyle.red,
                        emoji=self.bot.get_icon('control.resume', "▶️"),
                        custom_id="control.resume"
                    ),
                    Button(
                        style=ButtonStyle.blurple,
                        emoji=self.bot.get_icon('control.next', "⏭️"),
                        custom_id="control.next"
                    ),
                    Button(
                        style=[ButtonStyle.grey, ButtonStyle.green, ButtonStyle.blurple][self.loop],
                        emoji=self.bot.get_icon('control.repeat', "🔁"),
                        custom_id="control.repeat"
                    )
                ),
                ActionRow(
                    Button(
                        style=ButtonStyle.green if self.autoplay else ButtonStyle.grey,
                        emoji=self.bot.get_icon('control.autoplay', "🔥"),
                        custom_id="control.autoplay"
                    ),
                    Button(
                        style=ButtonStyle.blurple,
                        emoji=self.bot.get_icon('control.rewind', "⏪"),
                        custom_id="control.rewind"
                    ),
                    Button(
                        style=ButtonStyle.red,
                        emoji=self.bot.get_icon('control.stop', "⏹️"),
                        custom_id="control.stop"
                    ),
                    Button(
                        style=ButtonStyle.blurple,
                        emoji=self.bot.get_icon('control.forward', "⏩"),
                        custom_id="control.forward"
                    ),
                    Button(
                        style=ButtonStyle.grey,
                        emoji=self.bot.get_icon('empty', "⬛"),
                        custom_id="control.empty"
                    )
                )
            ]

        if interaction:
            await interaction.response.edit_message(
                embed=await self.__generate_display_embed(), components=components
            )

        else:
            await self.message.edit(embed=(await self.__generate_display_embed()), components=components)

        self.bot.logger.debug(
            "Updating player in guild %s display message to %s", self.bot.get_guild(self.guild_id), self.message.id
        )

    async def __generate_display_embed(self) -> Embed:
        """
        Generate the display embed for the player.

        :return: The generated embed
        """
        embed = Embed()

        if self.is_playing:
            embed.set_author(
                name=self.bot.get_text("display.status.playing", self.locale, "播放中"),
                icon_url="https://cdn.discordapp.com/emojis/987643956403781692.webp"
            )

            embed.colour = Colour.green()

        elif self.paused:
            embed.set_author(
                name=self.bot.get_text("display.status.paused", self.locale, "已暫停"),
                icon_url="https://cdn.discordapp.com/emojis/987661771609358366.webp"
            )

            embed.colour = Colour.orange()

        elif not self.is_connected:
            embed.set_author(
                name=self.bot.get_text("display.status.disconnected", self.locale, "已斷線"),
                icon_url="https://cdn.discordapp.com/emojis/987646268094439488.webp"
            )

            embed.colour = Colour.red()

        elif not self.current:
            embed.set_author(
                name=self.bot.get_text("display.status.ended", self.locale, "已結束"),
                icon_url="https://cdn.discordapp.com/emojis/987645074450034718.webp"
            )

            embed.colour = Colour.red()

        loop_mode_text = {
            0: self.bot.get_text('repeat_mode.off', self.locale, '關閉'),
            1: self.bot.get_text('repeat_mode.song', self.locale, '單曲'),
            2: self.bot.get_text('repeat_mode.queue', self.locale, '整個序列')
        }

        if self.current:
            embed.title = self.current.title
            embed.description = f"`{self.__format_time(self.position)}`" \
                                f" {self.__generate_progress_bar(self.current.duration, self.position)} " \
                                f"`{self.__format_time(self.current.duration)}`"

            embed.add_field(
                name=self.bot.get_text("display.author", self.locale, "👤 作者"), value=self.current.author, inline=True
            )

            embed.add_field(
                name=self.bot.get_text("display.requester", self.locale, "👥 點播者"),
                value=self.bot.get_text(
                    "display.requester.autoplay", self.locale, "自動播放"
                ) if not self.current.requester else f"<@{self.current.requester}>",
                inline=True
            )  # Requester will be 0 if the song is added by autoplay

            embed.add_field(
                name=self.bot.get_text("display.repeat_mode", self.locale, "🔁 重複播放模式"),
                value=loop_mode_text[self.loop],
                inline=True
            )

            queue_titles = [f"**[{index + 1}]** {track.title}" for index, track in enumerate(self.queue[:5])]
            queue_display = '\n'.join(queue_titles)

            if len(self.queue) > 5:
                queue_display += f"\n{self.bot.get_text('display.queue.more', self.locale, '還有更多...')}"

            embed.add_field(
                name=self.bot.get_text("display.queue", self.locale, "📃 播放序列"),
                value=queue_display or self.bot.get_text("empty", self.locale, "空"),
                inline=True
            )

            embed.add_field(
                name=self.bot.get_text("display.filters", self.locale, "⚙️ 已啟用效果器"),
                value=', '.join([key.capitalize() for key in self.filters]) or
                      self.bot.get_text("none", self.locale, "無"),
                inline=True
            )

            embed.add_field(
                name=self.bot.get_text("display.shuffle", self.locale, "🔀 隨機播放"),
                value=self.bot.get_text("display.enable", self.locale, "開啟")
                if self.shuffle else self.bot.get_text("display.disable", self.locale, "關閉"),
                inline=True
            )

            embed.set_footer(
                text=self.bot.get_text(
                    "display.footer", self.locale, "如果你覺得音樂怪怪的，可以試著檢查看看效果器設定或是切換語音頻道地區"
                )
            )

            if self.current.artwork_url:
                if await self.is_current_artwork_wide():
                    embed.set_image(self.current.artwork_url)
                else:
                    embed.set_thumbnail(self.current.artwork_url)

        else:
            embed.title = self.bot.get_text("error.nothing_playing", self.locale, "沒有正在播放的音樂")

        return embed

    @staticmethod
    def __format_time(time_ms: Union[float, int]) -> str:
        """
        Formats the time into DD:HH:MM:SS

        :param time_ms: Time in milliseconds
        :return: Formatted time
        """
        days, hours, minutes, seconds = parse_time(round(time_ms))

        days, hours, minutes, seconds = map(round, (days, hours, minutes, seconds))

        return ((f"{str(hours).zfill(2)}:" if hours else "")
                + f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}")

    def __generate_progress_bar(self, duration: Union[float, int], position: Union[float, int]):
        """
        Generate a progress bar.

        :param duration: The duration of the song.
        :param position: The current position of the song.
        :return: The progress bar.
        """
        duration = round(duration / 1000)
        position = round(position / 1000)

        if duration == 0:
            duration += 1

        percentage = position / duration

        return f"{self.bot.get_icon('progress.start_point', 'ST|')}" \
               f"{self.bot.get_icon('progress.start_fill', 'SF|') * round(percentage * 10)}" \
               f"{self.bot.get_icon('progress.mid_point', 'MP|') if percentage != 1 else self.bot.get_icon('progress.start_fill', 'SF|')}" \
               f"{self.bot.get_icon('progress.end_fill', 'EF|') * round((1 - percentage) * 10)}" \
               f"{self.bot.get_icon('progress.end', 'ED|') if percentage != 1 else self.bot.get_icon('progress.end_point', 'EP')}"

    def enter_disconnect_timeout(self):
        """
        Disconnect the player if it has been inactive for 5 minutes.
        """
        if self.timeout_task and not self.timeout_task.done():
            return

        self.timeout_task = self.bot.loop.create_task(self.__disconnect_timeout())

    def stop_disconnect_timeout(self):
        """
        Stop the disconnect timeout if it is running.
        """
        if self.timeout_task:
            self.timeout_task.cancel()

    async def __disconnect_timeout(self):
        except asyncio.TimeoutError:
        await asyncio.sleep(10)

        if self.message:
            await self.message.channel.send(
                embed=ErrorEmbed(
                    self.bot.get_text("timeout.disconnect", self.locale, "因為閒置超過 3 分鐘，已自動斷線")
                )
            )

        await asyncio.sleep(10)

        await self.guild.voice_client.disconnect(force=False)

        return

    async def is_current_artwork_wide(self) -> bool:
        """
        Check if the current playing track's artwork is wide.
        """
        if not self.current:
            return False

        if not self.current.artwork_url:
            return False

        if self.__last_image_url == self.current.artwork_url:
            return self.__display_image_as_wide

        self.__last_image_url = self.current.artwork_url

        width, height = await get_image_size(self.current.artwork_url)

        self.__display_image_as_wide = width > height

        return self.__display_image_as_wide

    async def _update_state(self, state: dict):
        """
        Updates the position of the player.

        Parameters
        ----------
        state: :class:`dict`
            The state that is given to update.
        """
        self._last_update = int(time() * 1000)
        self._last_position = state.get('position', 0)
        self.position_timestamp = state.get('time', 0)

        _ = self.bot.loop.create_task(self.check_autoplay())
        _ = self.bot.loop.create_task(self.update_display())

        if self.is_playing and not self.paused:
            self.stop_disconnect_timeout()
        else:
            self.enter_disconnect_timeout()
