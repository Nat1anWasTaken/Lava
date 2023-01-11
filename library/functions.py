import asyncio
from typing import Union, Iterable

from disnake import Interaction, Message, Thread, TextChannel, Embed, NotFound, Colour, ButtonStyle
from disnake.abc import GuildChannel
from disnake.ui import Button, ActionRow
from disnake.utils import get
from lavalink import DefaultPlayer, parse_time, DeferredAudioTrack, LoadResult

from core.classes import Bot
from library.classes import LavalinkVoiceClient
from library.errors import UserNotInVoice, MissingVoicePermissions, BotNotInVoice, UserInDifferentChannel
from library.sources.track import SpotifyAudioTrack


def split_list(input_list, chunk_size) -> Iterable[list]:
    length = len(input_list)

    num_sublists = length // chunk_size

    for i in range(num_sublists):
        yield input_list[i * chunk_size:(i + 1) * chunk_size]

    if length % chunk_size != 0:
        yield input_list[num_sublists * chunk_size:]


async def ensure_voice(interaction: Interaction, should_connect: bool) -> LavalinkVoiceClient:
    """
    This check ensures that the bot and command author are in the same voice channel.

    :param interaction: The interaction that triggered the command.
    :param should_connect: Whether the bot should connect to the voice channel if it isn't already connected.
    """
    player = interaction.bot.lavalink.player_manager.create(interaction.author.guild.id)

    if not interaction.author.voice or not interaction.author.voice.channel:
        raise UserNotInVoice('Please join a voice channel first')

    v_client = get(interaction.bot.voice_clients, guild=interaction.author.guild)

    if not v_client:
        if not should_connect:
            raise BotNotInVoice('Bot is not in a voice channel.')

        permissions = interaction.author.voice.channel.permissions_for(
            interaction.author.guild.get_member(interaction.bot.user.id)
        )

        if not permissions.connect or not permissions.speak:  # Check user limit too?
            raise MissingVoicePermissions('Connect and Speak permissions is required in order to play music')

        player.store('channel', interaction.channel.id)

        # noinspection PyTypeChecker
        return await interaction.author.voice.channel.connect(cls=LavalinkVoiceClient)

    if v_client.channel.id != interaction.author.voice.channel.id:
        raise UserInDifferentChannel(
            v_client.channel, "User must be in the same voice channel as the bot"
        )


def toggle_autoplay(player: DefaultPlayer) -> None:
    """
    Toggle autoplay for the player.

    :param player: The player instance.
    """

    if player.fetch("autoplay"):
        player.delete("autoplay")

        for item in player.queue:  # Remove songs added by autoplay
            if not item.requester:
                player.queue.remove(item)

    else:
        player.store("autoplay", "1")


async def get_recommended_tracks(bot: Bot,
                                 player: DefaultPlayer,
                                 tracks: list[DeferredAudioTrack],
                                 amount: int = 10) -> list[SpotifyAudioTrack]:
    """
    Get recommended tracks from the given track.

    :param bot: The bot instance.
    :param player: The player instance.
    :param tracks: The seed tracks to get recommended tracks from.
    :param amount: The amount of recommended tracks to get.
    """
    seed_tracks = []

    for track in tracks:
        if not isinstance(track, SpotifyAudioTrack):
            try:
                result = bot.spotify.search(f"{track.title} by {track.author}", type="track", limit=1)

                seed_tracks.append(result["tracks"]["items"][0]["id"])

            except IndexError:
                continue

            continue

        seed_tracks.append(track.identifier)

    recommendations = bot.spotify.recommendations(seed_tracks=seed_tracks, limit=amount)

    output = []

    for track in recommendations["tracks"]:
        load_result: LoadResult = await player.node.get_tracks(track['external_urls']['spotify'], check_local=True)

        output.append(load_result.tracks[0])

    return output


async def update_display(bot: Bot, player: DefaultPlayer, new_message: Message = None, delay: int = 0,
                         interaction: Interaction = None) -> None:
    """
    Update the display of the current song.

    Note: If new message is provided, Old message will be deleted after 5 seconds

    :param bot: The bot instance.
    :param player: The player instance.
    :param new_message: The new message to update the display with, None to use the old message.
    :param delay: The delay in seconds before updating the display.
    :param interaction: The interaction to be responded to.
    """
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
            await message.delete()
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
                    custom_id="control.autoplay"
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

    player.store('message', message.id)


def generate_display_embed(bot: Bot, player: DefaultPlayer) -> Embed:
    # TODO: Complete this embed
    embed = Embed()

    if player.is_playing:
        embed.set_author(name='播放中', icon_url="https://cdn.discordapp.com/emojis/987643956403781692.webp")

        embed.colour = Colour.green()

    elif player.paused:
        embed.set_author(name='已暫停', icon_url="https://cdn.discordapp.com/emojis/987661771609358366.webp")

        embed.colour = Colour.orange()

    elif not player.is_connected:
        embed.set_author(name='已斷線', icon_url="https://cdn.discordapp.com/emojis/987646268094439488.webp")

        embed.colour = Colour.red()

    elif not player.current:
        embed.set_author(name='已結束', icon_url="https://cdn.discordapp.com/emojis/987645074450034718.webp")

        embed.colour = Colour.red()

    loop_mode_text = {
        0: "關閉",
        1: "單曲循環",
        2: "整個佇列循環"
    }

    if player.current:
        embed.title = player.current.title
        embed.description = f"`{format_time(player.position)}`" \
                            f" {generate_progress_bar(bot, player.current.duration, player.position)} " \
                            f"`{format_time(player.current.duration)}`"

        embed.add_field(name="👤 作者", value=player.current.author, inline=True)
        embed.add_field(
            name="👥 點播者", value="自動播放" if not player.current.requester else f"<@{player.current.requester}>",
            inline=True
        )  # Requester will be 0 if the song is added by autoplay
        embed.add_field(name="🔁 重複播放模式", value=loop_mode_text[player.loop], inline=True)

        embed.add_field(
            name="📃 播放序列",
            value=('\n'.join(
                [
                    f"**[{index + 1}]** {track.title}"
                    for index, track in enumerate(player.queue[:5])
                ]
            ) + ("\n還有更多..." if len(player.queue) > 5 else "")) or "空",
            inline=True
        )
        embed.add_field(
            name="⚙️ 已啟用效果器",
            value=', '.join([key.capitalize() for key in player.filters]) or "無",
            inline=True
        )
        embed.add_field(name="🔀 隨機播放", value="開" if player.shuffle else "關", inline=True)

        embed.set_footer(text="如果你覺得音樂怪怪的，可以試著檢查看看效果器設定或是切換語音頻道地區")

    else:
        embed.title = "未在播放歌曲"

    return embed


def format_time(time: Union[float, int]) -> str:
    """
    Formats the time into DD:HH:MM:SS
    :param time: Time in milliseconds
    :return: Formatted time
    """
    days, hours, minutes, seconds = parse_time(round(time))

    days, hours, minutes, seconds = map(round, (days, hours, minutes, seconds))

    return f"{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"


def generate_progress_bar(bot: Bot, duration: Union[float, int], position: Union[float, int]):
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
