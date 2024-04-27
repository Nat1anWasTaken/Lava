from typing import TYPE_CHECKING, Optional, Dict

from lavalink import PlayerManager, Node, ClientError, Client

from lava.classes.player import LavaPlayer

if TYPE_CHECKING:
    from lava.bot import Bot


class LavaPlayerManager(PlayerManager):
    """The custom implemented PlayerManager for Lava"""

    def __init__(self, bot: "Bot", client: Client):
        """
        Initialize the LavaPlayerManager.

        :param bot: The Bot instance.
        :param client: The LavalinkClient instance.
        """
        super().__init__(client, LavaPlayer)

        self.bot: "Bot" = bot
        self.players: Dict[int, LavaPlayer] = {}

    def new(self,
            guild_id: int,
            *,
            region: Optional[str] = None,
            endpoint: Optional[str] = None,
            node: Optional[Node] = None) -> LavaPlayer:
        """
        Creates a new LavaPlayer for the given guild.

        This method is basically same as the original PlayerManager.create(),
        but without the unnecessary `cls` parameter.

        :param guild_id: The guild id to create the player for.
        :param region: The region to prioritize when choosing a node to connect to. If not specified,
            the region is determined from the `endpoint` parameter.
        :param endpoint: The endpoint to prioritize when choosing a node to connect to.
            This is useful when the region of the guild is not known.
        :param node: The node to use to create the player.
            If not specified, this method will find the best node to use based on the given `region` or `endpoint`.
        :return: The LavaPlayer instance that was created or already existed.
        :raise ClientError: If no available nodes are found.
        """
        if guild_id in self.players:
            return self.players[guild_id]

        if endpoint:  # Prioritise endpoint over region parameter
            region = self.client.node_manager.get_region(endpoint)

        best_node = node or self.client.node_manager.find_ideal_node(region)

        if not best_node:
            raise ClientError('No available nodes!')

        self.players[guild_id] = player = LavaPlayer(self.bot, guild_id, best_node)

        self.bot.logger.debug('Created player with GuildId %d on node \'%s\'', guild_id, best_node.name)

        return player

    def get(self, guild_id: int) -> Optional[LavaPlayer]:
        """
        Get the player for specific guild.

        :param guild_id: The guild id that the player belongs to.
        :return: The found LavaPlayer instance if found
        """
        return self.players.get(guild_id)
