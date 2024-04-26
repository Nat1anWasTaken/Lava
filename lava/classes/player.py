import asyncio
from typing import TYPE_CHECKING, Optional, Union

from disnake import Message, Interaction, Locale, TextChannel, Thread, NotFound, ButtonStyle, Embed, Colour
from disnake.abc import GuildChannel
from disnake.ui import ActionRow, Button
from lavalink import DefaultPlayer, Node, parse_time

from lava.variables import Variables

if TYPE_CHECKING:
    from lava.bot import Bot

class LavaPlayer(DefaultPlayer):
    def __init__(self, bot: "Bot", guild_id: int, node: Node):
        super().__init__(guild_id, node)

        self.bot: Bot = bot

    async def update_display(self,
                             player: "LavaPlayer",
                             new_message: Optional[Message] = None,
                             delay: int = 0,
                             interaction: Optional[Interaction] = None,
                             locale: Optional[Locale] = None) -> None:
        """
        Update the display of the current song.

        Note: If new message is provided, Old message will be deleted after 5 seconds

        :param bot: The bot instance.
        :param player: The player instance.
        :param new_message: The new message to update the display with, None to use the old message.
        :param delay: The delay in seconds before updating the display.
        :param interaction: The interaction to be responded to.
        :param locale: The locale to use.
        """
        if interaction:
            player.store("locale", interaction.locale)

        if locale:
            player.store("locale", locale)

        self.bot.logger.info(
            "Updating display for player in guild %s in a %s seconds delay", self.bot.get_guild(player.guild_id), delay
        )

        await asyncio.sleep(delay)

        # noinspection PyTypeChecker
        channel: Union[GuildChannel, TextChannel, Thread] = self.bot.get_channel(int(player.fetch('channel')))

        try:
            message: Message = await channel.fetch_message(int(player.fetch('message')))
        except (TypeError, NotFound):  # Message not found
            if not new_message:
                raise ValueError("No message found or provided to update the display with")

        if new_message:
            try:
                self.bot.logger.debug(
                    "Deleting old existing display message for player in guild %s", self.bot.get_guild(player.guild_id)
                )

                self.bot.loop.create_task(message.delete())
            except (AttributeError, UnboundLocalError):
                pass

            message = new_message

        if not player.is_connected or not player.current:
            components = []

        else:
            components = [
                ActionRow(
                    Button(
                        style=ButtonStyle.green if player.shuffle else ButtonStyle.grey,
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
                    ) if not player.paused else Button(
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
                        style=[ButtonStyle.grey, ButtonStyle.green, ButtonStyle.blurple][player.loop],
                        emoji=self.bot.get_icon('control.repeat', "🔁"),
                        custom_id="control.repeat"
                    )
                ),
                ActionRow(
                    Button(
                        style=ButtonStyle.green if player.fetch("autoplay") else ButtonStyle.grey,
                        emoji=self.bot.get_icon('control.autoplay', "🔥"),
                        custom_id="control.autoplay",
                        disabled=not bool(Variables.SPOTIFY_CLIENT)
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
            await interaction.response.edit_message(embed=self.generate_display_embed(self.bot, player), components=components)

        else:
            await message.edit(embed=self.generate_display_embed(self.bot, player), components=components)

        self.bot.logger.debug(
            "Updating player in guild %s display message to %s", self.bot.get_guild(player.guild_id), message.id
        )

        player.store('message', message.id)

    def generate_display_embed(self, bot: "Bot", player: DefaultPlayer) -> Embed:
        embed = Embed()

        locale: str = str(player.fetch("locale", "zh_TW"))

        if player.is_playing:
            embed.set_author(
                name=bot.get_text("display.status.playing", locale, "播放中"),
                icon_url="https://cdn.discordapp.com/emojis/987643956403781692.webp"
            )

            embed.colour = Colour.green()

        elif player.paused:
            embed.set_author(
                name=bot.get_text("display.status.paused", locale, "已暫停"),
                icon_url="https://cdn.discordapp.com/emojis/987661771609358366.webp"
            )

            embed.colour = Colour.orange()

        elif not player.is_connected:
            embed.set_author(
                name=bot.get_text("display.status.disconnected", locale, "已斷線"),
                icon_url="https://cdn.discordapp.com/emojis/987646268094439488.webp"
            )

            embed.colour = Colour.red()

        elif not player.current:
            embed.set_author(
                name=bot.get_text("display.status.ended", locale, "已結束"),
                icon_url="https://cdn.discordapp.com/emojis/987645074450034718.webp"
            )

            embed.colour = Colour.red()

        loop_mode_text = {
            0: bot.get_text('repeat_mode.off', locale, '關閉'),
            1: bot.get_text('repeat_mode.song', locale, '單曲'),
            2: bot.get_text('repeat_mode.queue', locale, '整個序列')
        }

        if player.current:
            embed.title = player.current.title
            embed.description = f"`{self.format_time(player.position)}`" \
                                f" {self.generate_progress_bar(bot, player.current.duration, player.position)} " \
                                f"`{self.format_time(player.current.duration)}`"

            embed.add_field(name=bot.get_text("display.author", locale, "👤 作者"), value=player.current.author, inline=True)
            embed.add_field(
                name=bot.get_text("display.requester", locale, "👥 點播者"),
                value=bot.get_text(
                    "display.requester.autoplay", locale, "自動播放"
                ) if not player.current.requester else f"<@{player.current.requester}>",
                inline=True
            )  # Requester will be 0 if the song is added by autoplay
            embed.add_field(
                name=bot.get_text("display.repeat_mode", locale, "🔁 重複播放模式"), value=loop_mode_text[player.loop],
                inline=True
            )

            embed.add_field(
                name=bot.get_text("display.queue", locale, "📃 播放序列"),
                value=('\n'.join(
                    [
                        f"**[{index + 1}]** {track.title}"
                        for index, track in enumerate(player.queue[:5])
                    ]
                ) + (f"\n{bot.get_text('display.queue.more', locale, '還有更多...')}" if len(player.queue) > 5 else "")) or
                    bot.get_text("empty", locale, "空"),
                inline=True
            )
            embed.add_field(
                name=bot.get_text("display.filters", locale, "⚙️ 已啟用效果器"),
                value=', '.join([key.capitalize() for key in player.filters]) or bot.get_text("none", locale, "無"),
                inline=True
            )
            embed.add_field(
                name=bot.get_text("display.shuffle", locale, "🔀 隨機播放"),
                value=bot.get_text("display.enable", locale, "開啟")
                if player.shuffle else bot.get_text("display.disable", locale, "關閉"),
                inline=True
            )

            embed.set_footer(
                text=bot.get_text(
                    "display.footer", locale, "如果你覺得音樂怪怪的，可以試著檢查看看效果器設定或是切換語音頻道地區"
                )
            )

        else:
            embed.title = bot.get_text("error.nothing_playing", locale, "沒有正在播放的音樂")

        return embed


    def format_time(self, time: Union[float, int]) -> str:
        """
        Formats the time into DD:HH:MM:SS
        :param time: Time in milliseconds
        :return: Formatted time
        """
        days, hours, minutes, seconds = parse_time(round(time))

        days, hours, minutes, seconds = map(round, (days, hours, minutes, seconds))

        return f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"


    def generate_progress_bar(self, bot: "Bot", duration: Union[float, int], position: Union[float, int]):
        """
        Generate a progress bar.

        :param bot: The bot instance.
        :param duration: The duration of the song.
        :param position: The current position of the song.
        :return: The progress bar.
        """
        duration = round(duration / 1000)
        position = round(position / 1000)

        if duration == 0:
            duration += 1

        percentage = position / duration

        return f"{bot.get_icon('progress.start_point', 'ST|')}" \
            f"{bot.get_icon('progress.start_fill', 'SF|') * round(percentage * 10)}" \
            f"{bot.get_icon('progress.mid_point', 'MP|') if percentage != 1 else bot.get_icon('progress.start_fill', 'SF|')}" \
            f"{bot.get_icon('progress.end_fill', 'EF|') * round((1 - percentage) * 10)}" \
            f"{bot.get_icon('progress.end', 'ED|') if percentage != 1 else bot.get_icon('progress.end_point', 'EP')}"