import asyncio
import json
import logging
import os
from os import getenv

from colorlog import ColoredFormatter
from disnake import Intents, Streaming, Activity, Game, ActivityType
from disnake.ext.commands import CommandSyncFlags
from dotenv import load_dotenv

from lava.bot import Bot


def main():
    load_dotenv("stack.env")

    setup_logging()

    main_logger = logging.getLogger("lava.main")

    loop = asyncio.new_event_loop()

    activity = set_activity()    

    bot = Bot(
        logger=main_logger,
        command_prefix=getenv("PREFIX", "l!"),
        intents=Intents.all(),
        loop=loop,
        activity=activity,
        command_sync_flags=CommandSyncFlags.default(),
    )

    bot.i18n.load("locale/")

    load_extensions(bot)

    bot.run(os.environ["TOKEN"])


def set_activity():
    with open("configs/activity.json", "r") as f:
        activity = json.load(f)

    status = activity["status"]
    name = activity["name"]

    match status:
        case "playing":
            activity = Game(name=name)
        case "listening":
            activity = Activity(type=ActivityType.listening, name=name)
        case "streaming":
            activity = Streaming(name=name, url=activity["url"])
        case "watching":
            activity = Activity(type=ActivityType.watching, name=name)

    return activity


def setup_logging():
    """
    Set up the loggings for the bot
    :return: None
    """
    formatter = ColoredFormatter(
        "%(asctime)s %(log_color)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(filename="lava.log", encoding="utf-8", mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logging.basicConfig(handlers=[stream_handler, file_handler], level=logging.INFO)


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
