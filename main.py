import json
import logging
from os import getenv

from disnake import Intents
from disnake.ext.commands import CommandSyncFlags

from core.classes import Bot

logging.basicConfig(level=logging.INFO)


def main():
    bot = setup_bot()

    load_extensions(bot)

    load_lavalink_nodes(bot)

    bot.run(getenv("BOT_TOKEN"))


def setup_bot() -> Bot:
    """
    Set up the bot
    :return: The bot
    """
    bot = Bot(command_prefix=getenv("PREFIX", "l!"), intents=Intents.all(), command_sync_flags=CommandSyncFlags.all())

    return bot


def load_lavalink_nodes(bot: Bot) -> Bot:
    """
    Load lavalink nodes from the lavalink.json file
    :return: The bot
    """
    with open("lavalink.json", "r") as f:
        config = json.load(f)

    for node in config['nodes']:
        bot.lavalink.add_node(**node)

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
