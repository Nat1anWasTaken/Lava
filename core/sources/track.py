from logging import getLogger

from lavalink import DeferredAudioTrack, LoadResult, LoadType, LoadError


class SpotifyAudioTrack(DeferredAudioTrack):
    async def load(self, client):  # skipcq: PYL-W0201
        getLogger('lava.sources').info(
            "Loading spotify track %s...", self.title)

        result: LoadResult = await client.get_tracks(
            f'ytsearch:{self.title} {self.author}'
        )

        if result.load_type != LoadType.SEARCH or not result.tracks:
            raise LoadError

        first_track = result.tracks[0]
        base64 = first_track.track
        self.track = base64

        getLogger('lava.sources').info("Loaded spotify track %s", self.title)

        return base64
