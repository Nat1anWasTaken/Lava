import re
from asyncio import sleep

from disnake import Option, ApplicationCommandInteraction, OptionType
from disnake.ext import commands
from disnake.ext.commands import Cog
from lavalink import DefaultPlayer, LoadResult, LoadType

from core.classes import Bot
from core.embeds import ErrorEmbed, SuccessEmbed
from library.functions import ensure_voice, update_display


class Commands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.slash_command(
        name="play",
        description="播放一首歌曲",
        options=[
            Option(
                name="query",
                description="歌曲名稱或網址，支援 YouTube, YouTube Music, SoundCloud, Spotify",
                type=OptionType.string,
                required=True
            ),
            Option(
                name="index",
                description="要將歌曲放置於當前播放序列的位置",
                type=OptionType.integer,
                required=False
            )
        ]
    )
    async def play(self, interaction: ApplicationCommandInteraction, query: str, index: int = None):
        await interaction.response.defer()

        await ensure_voice(interaction, should_connect=True)

        player: DefaultPlayer = self.bot.lavalink.player_manager.get(interaction.guild.id)

        player.store("channel", interaction.channel.id)

        url_rx = re.compile(r"https?://(?:www\.)?.+")

        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results: LoadResult = await player.node.get_tracks(query)

        if not results or not results.tracks:
            return await interaction.edit_original_response(embed=ErrorEmbed("沒有找到任何歌曲"))

        match results.load_type:
            case LoadType.TRACK:
                player.add(requester=interaction.author.id, track=results.tracks[0], index=index)

                await interaction.edit_original_response(
                    embed=SuccessEmbed(f"已加入播放序列", f"{results.tracks[0].title}")
                )

            case LoadType.PLAYLIST:
                # TODO: Ask user if they want to add the whole playlist or just some tracks

                for iter_index, track in enumerate(results.tracks):
                    player.add(requester=interaction.author.id, track=track, index=index + iter_index)

                await interaction.edit_original_response(
                    embed=SuccessEmbed(
                        f"已將 {results.playlist_info.name} 中的 {len(results.tracks)} 首歌曲加入播放序列",
                        '\n'.join([f"{index + 1}. {track.title}" for index, track in enumerate(results.tracks)])
                    )
                )

        # If the player isn't already playing, start it.
        if not player.is_playing:
            await player.play()

        await sleep(5)

        await update_display(self.bot, player, await interaction.original_response())


def setup(bot):
    bot.add_cog(Commands(bot))
