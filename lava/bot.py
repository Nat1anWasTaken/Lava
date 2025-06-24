import asyncio
import json
import logging
import os
from logging import Logger
from typing import Optional

from disnake import Locale
from disnake.ext.commands import Bot as OriginalBot

from lava.classes.lavalink_client import LavalinkClient
from lava.source import SourceManager


class Bot(OriginalBot):
    def __init__(self, logger: Logger, **kwargs):
        super().__init__(**kwargs)

        self.logger = logger

        self._lavalink: Optional[LavalinkClient] = None

        self.api = None
        self.api_server_task = None
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))

        with open("configs/icons.json", "r", encoding="utf-8") as f:
            self.icons = json.load(f)

    async def on_ready(self):
        self.logger.info("The bot is ready! Logged in as %s" % self.user)

        self.__setup_lavalink_client()
        await self.__setup_api_server()

    @property
    def lavalink(self) -> LavalinkClient:
        if not self.is_ready():
            raise RuntimeError("The bot is not ready yet!")

        if self._lavalink is None:
            self.__setup_lavalink_client()

        return self._lavalink

    def __setup_lavalink_client(self):
        """
        Sets up the lavalink client for the bot
        :return: Lavalink Client
        """
        self.logger.info("Setting up lavalink client...")

        self._lavalink = LavalinkClient(self, user_id=self.user.id)

        self.logger.info("Loading lavalink nodes...")

        with open("configs/lavalink.json", "r") as f:
            config = json.load(f)

        for node in config["nodes"]:
            self.logger.debug("Adding lavalink node %s", node["host"])

            self.lavalink.add_node(**node)

        self.logger.info("Done loading lavalink nodes!")

        self.lavalink.register_source(SourceManager())

    async def __setup_api_server(self):
        """
        Sets up and starts the API server
        """
        try:
            from lava.api import setup_api

            self.logger.info("Setting up API server...")

            self.api = setup_api(self)

            self.api_server_task = asyncio.create_task(
                self.api.start_server(host=self.api_host, port=self.api_port)
            )

            self.logger.info(f"API server started on {self.api_host}:{self.api_port}")
            self.logger.info(
                f"API documentation available at http://{self.api_host}:{self.api_port}/docs"
            )

        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")

    async def close(self):
        """
        Clean shutdown of the bot and API server
        """
        self.logger.info("Shutting down bot...")

        if self.api_server_task:
            self.logger.info("Stopping API server...")
            self.api_server_task.cancel()
            try:
                await self.api_server_task
            except asyncio.CancelledError:
                pass
            self.logger.info("API server stopped")

        await super().close()

    def get_text(self, key: str, locale: Locale, default: str = None) -> str:
        """
        Gets a text from i18n files by key
        :param key: The key of the text
        :param locale: The locale of the text
        :param default: The default value to return if the text is not found
        :return: The text
        """
        return self.i18n.get(key).get(str(locale), default)

    def get_icon(self, name: str, default: any) -> any:
        """
        Get an icon
        :param name: The name of the icon
        :param default: The default value to return if the icon is not found
        :return: The icon
        """
        dct = self.icons.copy()

        for key in name.split("."):
            try:
                dct = dct[key]
            except KeyError:
                return default

        return dct
