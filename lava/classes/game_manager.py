from typing import TYPE_CHECKING, Optional, Dict

from lava.classes.game import Game
from disnake import TextChannel

if TYPE_CHECKING:
    from lava.bot import Bot


class GameManager:
    """The custom implemented GameManager for Lava"""

    def __init__(self, bot: "Bot"):
        """
        Initialize the GameManager.
        """
        self.bot: "Bot" = bot
        self.games: Dict[int, Game] = {}

    def new(self,
            guild_id: int,
            title: str,
            genre: str,
            channel: TextChannel,
            rounds: int,
            round_delay: int,
            round_length: int,
            victory_score: int,
            match_percentage: float,
        ) -> Game:
        """
        Creates a new Game for the given guild.

        :param guild_id: The guild id to create the Game for.
        """
        if guild_id in self.games:
            return self.games[guild_id]

        self.games[guild_id] = game = Game(guild_id, title, genre, channel, rounds, round_delay, round_length, victory_score, match_percentage)

        self.bot.logger.debug('Created Game with GuildId %d ', guild_id)

        return game

    def get(self, guild_id: int) -> Optional[Game]:
        """
        Get the Game for specific guild.

        :param guild_id: The guild id that the game belongs to.
        :return: The found Game instance if found
        """
        return self.games.get(guild_id)
