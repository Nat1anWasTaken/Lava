import re

from disnake import Option, ApplicationCommandInteraction, Embed, Color
from disnake.ext import commands
from disnake.ext.commands import Cog

from library.functions import ensure_voice


class Commands(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="play",
        description="播放一首歌曲",
        options=[
            Option(
                name="query",
                description="歌曲名稱或網址，支援 YouTube, YouTube Music, SoundCloud, Spotify",
            )
        ]
    )
    async def play(self, interaction: ApplicationCommandInteraction, query: str):
        await ensure_voice(self.bot, interaction.author, interaction.channel, should_connect=True)

        player = self.bot.lavalink.player_manager.get(interaction.guild.id)

        url_rx = re.compile(r"https?://(?:www\.)?.+")

        # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
        # SoundCloud searching is possible by prefixing "scsearch:" instead.
        if not url_rx.match(query):
            query = f'ytsearch:{query}'

        # Get the results for the query from Lavalink.
        results = await player.node.get_tracks(query)

        # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
        # Alternatively, results.tracks could be an empty array if the query yielded no tracks.
        if not results or not results.tracks:
            return await interaction.response.send_message('Nothing found!', ephemeral=True)

        embed = Embed(color=Color.blurple())

        # Valid loadTypes are:
        #   TRACK_LOADED    - single video/direct URL)
        #   PLAYLIST_LOADED - direct URL to playlist)
        #   SEARCH_RESULT   - query prefixed with either ytsearch: or scsearch:.
        #   NO_MATCHES      - query yielded no results
        #   LOAD_FAILED     - most likely, the video encountered an exception during loading.
        if results.load_type == 'PLAYLIST_LOADED':
            tracks = results.tracks

            for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                player.add(requester=interaction.author.id, track=track)

            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
        else:
            track = results.tracks[0]
            embed.title = 'Track Enqueued'
            embed.description = f'[{track.title}]({track.uri})'

            player.add(requester=interaction.author.id, track=track)

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # If the player isn't already playing, start it.
        if not player.is_playing:
            await player.play()


def setup(bot):
    bot.add_cog(Commands(bot))
