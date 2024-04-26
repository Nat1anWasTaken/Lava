import asyncio
from typing import TYPE_CHECKING, Optional, Union

from disnake import Message, Interaction, Locale, TextChannel, Thread, NotFound
from disnake.abc import GuildChannel
from disnake.ui import ActionRow
from lavalink import DefaultPlayer, Node

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
            "Updating display for player in guild %s in a %s seconds delay", bot.get_guild(player.guild_id), delay
        )

        await asyncio.sleep(delay)

        # noinspection PyTypeChecker
        channel: Union[GuildChannel, TextChannel, Thread] = bot.get_channel(int(player.fetch('channel')))

        try:
            message: Message = await channel.fetch_message(int(player.fetch('message')))
        except (TypeError, NotFound):  # Message not found
            if not new_message:
                raise ValueError("No message found or provided to update the display with")

        if new_message:
            try:
                bot.logger.debug(
                    "Deleting old existing display message for player in guild %s", bot.get_guild(player.guild_id)
                )

                bot.loop.create_task(message.delete())
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
                        emoji=bot.get_icon('control.shuffle', "🔀"),
                        custom_id="control.shuffle"
                    ),
                    Button(
                        style=ButtonStyle.blurple,
                        emoji=bot.get_icon('control.previous', "⏮️"),
                        custom_id="control.previous"
                    ),
                    Button(
                        style=ButtonStyle.green,
                        emoji=bot.get_icon('control.pause', "⏸️"),
                        custom_id="control.pause"
                    ) if not player.paused else Button(
                        style=ButtonStyle.red,
                        emoji=bot.get_icon('control.resume', "▶️"),
                        custom_id="control.resume"
                    ),
                    Button(
                        style=ButtonStyle.blurple,
                        emoji=bot.get_icon('control.next', "⏭️"),
                        custom_id="control.next"
                    ),
                    Button(
                        style=[ButtonStyle.grey, ButtonStyle.green, ButtonStyle.blurple][player.loop],
                        emoji=bot.get_icon('control.repeat', "🔁"),
                        custom_id="control.repeat"
                    )
                ),
                ActionRow(
                    Button(
                        style=ButtonStyle.green if player.fetch("autoplay") else ButtonStyle.grey,
                        emoji=bot.get_icon('control.autoplay', "🔥"),
                        custom_id="control.autoplay",
                        disabled=not bool(Variables.SPOTIFY_CLIENT)
                    ),
                    Button(
                        style=ButtonStyle.blurple,
                        emoji=bot.get_icon('control.rewind', "⏪"),
                        custom_id="control.rewind"
                    ),
                    Button(
                        style=ButtonStyle.red,
                        emoji=bot.get_icon('control.stop', "⏹️"),
                        custom_id="control.stop"
                    ),
                    Button(
                        style=ButtonStyle.blurple,
                        emoji=bot.get_icon('control.forward', "⏩"),
                        custom_id="control.forward"
                    ),
                    Button(
                        style=ButtonStyle.grey,
                        emoji=bot.get_icon('empty', "⬛"),
                        custom_id="control.empty"
                    )
                )
            ]

        if interaction:
            await interaction.response.edit_message(embed=generate_display_embed(bot, player), components=components)

        else:
            await message.edit(embed=generate_display_embed(bot, player), components=components)

        bot.logger.debug(
            "Updating player in guild %s display message to %s", bot.get_guild(player.guild_id), message.id
        )

        player.store('message', message.id)
