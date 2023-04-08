import asyncio
import json
import logging
import os
from os import getenv

from disnake import Intents
from disnake.ext.commands import CommandSyncFlags
from dotenv import load_dotenv

from core.classes import Bot

logging.basicConfig(level=logging.INFO)


def main():
    load_dotenv()

    loop = asyncio.new_event_loop()

    bot = Bot(
        command_prefix=getenv("PREFIX", "l!"), intents=Intents.all(), loop=loop,
        command_sync_flags=CommandSyncFlags.default()
    )

    load_extensions(bot)

    bot.run(os.environ["TOKEN"])


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
