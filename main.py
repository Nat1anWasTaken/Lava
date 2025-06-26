import asyncio
import json
import logging
import os
from os import getenv

from colorlog import ColoredFormatter
from disnake import Intents, Activity, BaseActivity
from disnake.ext.commands import CommandSyncFlags
from dotenv import load_dotenv

from lava.bot import Bot


def main():
    if getenv("LOAD_ENV", "true").lower() == "true":
        load_dotenv("stack.env")

    setup_logging()

    main_logger = logging.getLogger("lava.main")

    loop = asyncio.new_event_loop()

    bot = Bot(
        logger=main_logger,
        command_prefix=getenv("PREFIX", "l!"),
        intents=Intents.all(),
        loop=loop,
        activity=get_activity(),
        command_sync_flags=CommandSyncFlags.default(),
    )

    bot.i18n.load("locale/")

    load_extensions(bot)

    bot.run(os.environ["TOKEN"])


def get_activity() -> BaseActivity:
    with open("configs/activity.json", "r") as f:
        activity = json.load(f)

    return Activity(**activity)


def setup_logging():
    """
    Set up the loggings for the bot
    :return: None
    """
    formatter = ColoredFormatter(
        '%(asctime)s %(log_color)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'white',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(filename="lava.log", encoding="utf-8", mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        handlers=[stream_handler, file_handler], level=logging.INFO
    )


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
