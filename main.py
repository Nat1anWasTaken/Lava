import asyncio
import json
import logging
from os import getenv

from disnake import Intents
from disnake.ext.commands import CommandSyncFlags
from lavalink import Client
from spotipy import Spotify, SpotifyClientCredentials

from core.classes import Bot
from library.classes import SpotifySource

logging.basicConfig(level=logging.INFO)


def main():
    loop = asyncio.new_event_loop()

    bot = Bot(
        command_prefix=getenv("PREFIX", "l!"), intents=Intents.all(),
        command_sync_flags=CommandSyncFlags.all(), loop=loop
    )

    loop.create_task(setup_bot(bot))

    bot.run(getenv("TOKEN"))


async def setup_bot(bot: Bot) -> Bot:
    await bot.wait_until_ready()

    load_extensions(bot)

    load_lavalink_nodes(bot)

    if getenv("SPOTIFY_CLIENT_ID") and getenv("SPOTIFY_CLIENT_SECRET"):
        initial_spotify_source(bot)

    return bot


def load_lavalink_nodes(bot: Bot) -> Bot:
    """
    Create a lavalink client then load lavalink nodes from the lavalink.json file
    :return: The bot
    """
    bot.assign_lavalink_client(Client(bot.user.id))

    with open("lavalink.json", "r") as f:
        config = json.load(f)

    for node in config['nodes']:
        bot.lavalink.add_node(**node)

    return bot


def initial_spotify_source(bot: Bot) -> Bot:
    """
    Initialize the spotify source then register it to the bot

    Note: bot.assign_lavalink_client() must be called before this function
    :param bot: The bot to register the spotify source to
    :return: The bot
    """
    credentials = SpotifyClientCredentials(
        client_id=getenv("SPOTIFY_CLIENT_ID"),
        client_secret=getenv("SPOTIFY_CLIENT_SECRET")
    )

    spotify = Spotify(auth_manager=credentials)

    spotify_source = SpotifySource(spotify)

    bot.lavalink.register_source(spotify_source)

    return bot


def load_extensions(bot: Bot) -> Bot:
    """
    Load extensions in extensions.json file
    :param bot: The bot to load the extensions to
    :return: The bot
    """
    with open("extensions.json", "r") as f:
        extensions = json.load(f)

    for extension in extensions:
        bot.load_extension(extension)

    return bot


if __name__ == "__main__":
    main()
