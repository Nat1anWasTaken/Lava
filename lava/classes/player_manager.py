from typing import Optional, Dict

from lavalink import PlayerManager, Node, ClientError, Client

from lava.classes.player import LavaPlayer


class LavaPlayerManager(PlayerManager):
    """
    The custom implemented PlayerManager for Lava
    """

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
        This implement is basically same as the original PlayerManager.create(), but without the unnecessary `cls` parameter.

        :param guild_id: The guild id to create the player for.
        :param
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
