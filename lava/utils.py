import asyncio
import subprocess
from typing import Union, Iterable, Optional

from disnake import Interaction, Message, Thread, TextChannel, Embed, NotFound, Colour, ButtonStyle, Locale
from disnake.abc import GuildChannel
from disnake.ui import Button, ActionRow
from disnake.utils import get
from lavalink import DefaultPlayer, parse_time, DeferredAudioTrack, LoadResult
from spotipy import Spotify

from lava.bot import Bot
from lava.errors import UserNotInVoice, MissingVoicePermissions, BotNotInVoice, UserInDifferentChannel
from lava.source import SpotifyAudioTrack
from lava.variables import Variables
from lava.voice_client import LavalinkVoiceClient


def get_current_branch() -> str:
    """
    Get the current branch of the git repository
    :return: The current branch
    """
    output = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    return output.strip().decode()


def get_upstream_url(branch: str) -> Optional[str]:
    """
    Get the upstream url of the branch
    :param branch: The branch to get the upstream url of
    :return: The upstream url, or None if it doesn't exist
    """
    try:
        output = subprocess.check_output(['git', 'config', '--get', f'branch.{branch}.remote'])
    except subprocess.CalledProcessError:
        return None

    remote_name = output.strip().decode()

    output = subprocess.check_output(['git', 'config', '--get', f'remote.{remote_name}.url'])
    return output.strip().decode()


def get_commit_hash() -> str:
    """
    Get the commit hash of the current commit.
    :return: The commit hash
    """
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()


def bytes_to_gb(bytes_: int) -> float:
    """
    Convert bytes to gigabytes.

    :param bytes_: The number of bytes.
    """
    return bytes_ / 1024 ** 3


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


async def get_recommended_tracks(spotify: Spotify,
                                 player: DefaultPlayer,
                                 tracks: list[DeferredAudioTrack],
                                 amount: int = 10) -> list[SpotifyAudioTrack]:
    """
    Get recommended tracks from the given track.

    :param spotify: The spotify instance.
    :param player: The player instance.
    :param tracks: The seed tracks to get recommended tracks from.
    :param amount: The amount of recommended tracks to get.
    """
    seed_tracks = []

    for track in tracks:
        if not isinstance(track, SpotifyAudioTrack):
            try:
                result = spotify.search(f"{track.title} by {track.author}", type="track", limit=1)

                seed_tracks.append(result["tracks"]["items"][0]["id"])

            except IndexError:
                continue

            continue

        seed_tracks.append(track.identifier)

    recommendations = spotify.recommendations(seed_tracks=seed_tracks, limit=amount)

    output = []

    for track in recommendations["tracks"]:
        load_result: LoadResult = await player.node.get_tracks(track['external_urls']['spotify'], check_local=True)

        output.append(load_result.tracks[0])

    return output


async def update_display(bot: Bot, player: DefaultPlayer, new_message: Message = None, delay: int = 0,
                         interaction: Interaction = None, locale: Locale = None) -> None:
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

    bot.logger.info(
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

    bot.logger.debug("Updating player in guild %s display message to %s", bot.get_guild(player.guild_id), message.id)

    player.store('message', message.id)


def generate_display_embed(bot: Bot, player: DefaultPlayer) -> Embed:
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
        embed.description = f"`{format_time(player.position)}`" \
                            f" {generate_progress_bar(bot, player.current.duration, player.position)} " \
                            f"`{format_time(player.current.duration)}`"

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
