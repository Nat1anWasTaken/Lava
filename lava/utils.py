import subprocess
from bisect import bisect_left
from io import BytesIO
from typing import Iterable, Optional, TYPE_CHECKING, Tuple

import aiohttp
import imageio
from disnake import Interaction
from disnake.utils import get
from lavalink import AudioTrack, LoadResult
from pylrc.classes import LyricLine
from youtubesearchpython import VideosSearch

from lava.classes.voice_client import LavalinkVoiceClient
from lava.errors import UserNotInVoice, BotNotInVoice, MissingVoicePermissions, UserInDifferentChannel

if TYPE_CHECKING:
    from lava.classes.player import LavaPlayer


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
    :param should_connect: Should the bot connect to the channel if not connected.s
    """
    if not interaction.author.voice or not interaction.author.voice.channel:
        raise UserNotInVoice('Please join a voice channel first')

    voice_client = get(interaction.bot.voice_clients, guild=interaction.author.guild)

    if not voice_client:
        if not should_connect:
            raise BotNotInVoice('Bot is not in a voice channel.')

        permissions = interaction.author.voice.channel.permissions_for(
            interaction.author.guild.get_member(interaction.bot.user.id)
        )

        if not permissions.connect or not permissions.speak:  # Check user limit too?
            raise MissingVoicePermissions('Connect and Speak permissions is required in order to play music')

        # noinspection PyTypeChecker
        return await interaction.author.voice.channel.connect(cls=LavalinkVoiceClient)

    if voice_client.channel.id != interaction.author.voice.channel.id:
        raise UserInDifferentChannel(
            voice_client.channel, "User must be in the same voice channel as the bot"
        )


async def get_recommended_tracks(player: "LavaPlayer", track: AudioTrack, max_results: int) -> list[AudioTrack]:
    """
    Get recommended track from the given track.

    :param player: The player instance.
    :param track: The seed tracks to get recommended tracks from.
    :param max_results: The max amount of tracks to get.
    """
    results_from_yt: LoadResult = None

    if track.source_name != "youtube":
        videos_Search = VideosSearch(f"{track.title} by {track.author}", limit=1)
        track.identifier = videos_Search.result()['result'][0]['id']

    results_from_yt = await player.node.get_tracks(f"https://music.youtube.com/watch?v={track.identifier}8&list=RD{track.identifier}")

    results: list[AudioTrack] = []

    skip_first = True

    for result_track in results_from_yt.tracks:
        if skip_first:
            skip_first = False
            continue

        if result_track.identifier in [t.identifier for t in results]:  # Don't add duplicate songs
            continue

        if len(results) >= max_results:
            break

        results.append(result_track)

    return results


async def get_image_size(url: str) -> Optional[Tuple[int, int]]:
    """
    Get the size of the image from the given URL.

    :param url: The URL of the image.
    :return The width and height of the image. If the image is not found, return None.
    """
    async with aiohttp.ClientSession() as session, session.get(url) as response:
        if response.status != 200:
            return None

        data = await response.read()
        img = imageio.imread(BytesIO(data))

        return img.shape[1], img.shape[0]


def find_lyrics_within_range(lyrics: list[LyricLine], target_seconds: float, range_seconds: float) -> list[LyricLine]:
    """
    Find lyrics within a range of the target time.
    :param lyrics: The lyrics to search from.
    :param target_seconds: The target time in seconds.
    :param range_seconds: The range in seconds.
    :return: The lyrics within the range and the index of the closest lyric.
    """
    lyrics.sort(key=lambda x: x.time)

    start_index = bisect_left([lyric.time for lyric in lyrics], target_seconds)

    result = []

    for i in range(start_index, len(lyrics)):
        if lyrics[i].time - target_seconds > range_seconds:
            break
        if 0 <= lyrics[i].time - target_seconds <= range_seconds:
            result.append(lyrics[i])

    return result
