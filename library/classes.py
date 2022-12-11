import re
from typing import Union, Tuple

from disnake import VoiceClient, abc
from lavalink import DeferredAudioTrack, Source, LoadResult, PlaylistInfo, LoadType, Client, LoadError, DefaultPlayer
from spotipy import Spotify

from core.classes import Bot


class LavalinkVoiceClient(VoiceClient):
    """
    This is the preferred way to handle external voice sending
    This client will be created via a cls in the connect method of the channel
    see the following documentation:
    https://discordpy.readthedocs.io/en/latest/api.html#voiceprotocol
    """

    def __init__(self, bot: Bot, channel: abc.Connectable):
        self.bot = bot
        self.channel = channel
        self.lavalink = bot.lavalink

        super().__init__(bot, channel)

    async def on_voice_server_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.bot.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        # the data needs to be transformed before being handed down to
        # voice_update_handler
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False,
                      self_mute: bool = False) -> None:
        """
        Connect the bot to the voice channel and create a player_manager
        if it doesn't exist yet.
        """
        # ensure there is a player_manager when creating a new voice_client
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        """
        Handles the disconnect.
        Cleans up running player and leaves the voice client.
        """
        player: DefaultPlayer = self.lavalink.player_manager.get(self.channel.guild.id)

        # no need to disconnect if we are not connected
        if not force and not player.is_connected:
            return

        # None means disconnect
        await self.channel.guild.change_voice_state(channel=None)

        # update the channel_id of the player to None
        # this must be done because the on_voice_state_update that would set channel_id
        # to None doesn't get dispatched after the disconnect
        player.channel_id = None

        self.cleanup()


class SpotifyAudioTrack(DeferredAudioTrack):
    # A DeferredAudioTrack allows us to load metadata now, and a playback URL later.
    # This makes the DeferredAudioTrack highly efficient, particularly in cases
    # where large playlists are loaded.

    async def load(self, client):  # Load our 'actual' playback track using the metadata from this one.
        result: LoadResult = await client.get_tracks(
            f'ytsearch:{self.title} {self.author}'
        )  # Search for our track on YouTube.

        if result.load_type != LoadType.SEARCH or not result.tracks:  # We're expecting a 'SEARCH' due to our 'ytsearch' prefix above.
            raise LoadError

        first_track = result.tracks[0]  # Grab the first track from the results.
        base64 = first_track.track  # Extract the base64 string from the track.
        self.track = base64  # We'll store this for later, as it allows us to save making network requests
        # if this track is re-used (e.g. repeat).

        return base64


class SpotifySource(Source):
    def __init__(self, spotify: Spotify):
        super().__init__(name='spotify')  # Initialising our custom source with the name 'custom'.

        self.spotify = spotify

    async def load_item(self, client: Client, query: str):
        track = self.load_track(query)

        if track:
            return LoadResult(LoadType.TRACK, [track], playlist_info=PlaylistInfo.none())

        playlist, playlist_info = self.load_playlist(query)

        if playlist:
            return LoadResult(LoadType.PLAYLIST, playlist, playlist_info=playlist_info)

        album, playlist_info = self.load_album(query)

        if album:
            return LoadResult(LoadType.PLAYLIST, album, playlist_info=playlist_info)

        return None

    def load_track(self, url: str) -> Union[SpotifyAudioTrack, None]:
        """
        Get a track with given url from spotify, None if not found
        :param url: Spotify track url
        :return: SpotifyAudioTrack
        """
        track_id = self.get_track_id_from_url(url)

        if not track_id:
            return None

        track = self.spotify.track(track_id)

        if track:
            return SpotifyAudioTrack(
                {
                    'identifier': track['id'],
                    'isSeekable': True,
                    'author': ', '.join([artist['name'] for artist in track['artists']]),
                    'length': track['duration_ms'],
                    'isStream': False,
                    'title': track['name'],
                    'uri': f"https://open.spotify.com/track/{track['id']}"
                },
                requester=0
            )
        return None

    def load_playlist(self, url: str) -> Tuple[list[SpotifyAudioTrack], Union[PlaylistInfo, None]]:
        """
        Get tracks in a playlist with given url from spotify, None if not found
        :param url: Spotify playlist url
        :return: list[SpotifyAudioTrack], PlaylistInfo
        """
        playlist_id = self.get_playlist_id_from_url(url)

        if not playlist_id:
            return [], None

        playlist = self.spotify.playlist(playlist_id)

        playlist_info = PlaylistInfo(playlist['name'], -1)

        if playlist:
            tracks = []

            for track in playlist['tracks']['items']:
                tracks.append(
                    SpotifyAudioTrack(
                        {
                            'identifier': track['track']['id'],
                            'isSeekable': True,
                            'author': ', '.join([artist['name'] for artist in track['track']['artists']]),
                            'length': track['track']['duration_ms'],
                            'isStream': False,
                            'title': track['track']['name'],
                            'uri': f"https://open.spotify.com/track/{track['track']['id']}"
                        },
                        requester=0
                    )
                )

            return tracks, playlist_info
        return [], None

    def load_album(self, url: str) -> Tuple[list[SpotifyAudioTrack], Union[PlaylistInfo, None]]:
        """
        Get tracks in a album with given url from spotify, None if not found
        :param url: Spotify album url
        :return: list[SpotifyAudioTrack], PlaylistInfo
        """
        album_id = self.get_album_id_from_url(url)

        if not album_id:
            return [], None

        album = self.spotify.album(album_id)

        playlist_info = PlaylistInfo(album['name'], -1)

        if album:
            tracks = []

            for track in album['tracks']['items']:
                tracks.append(
                    SpotifyAudioTrack(
                        {
                            'identifier': track['id'],
                            'isSeekable': True,
                            'author': ', '.join([artist['name'] for artist in track['artists']]),
                            'length': track['duration_ms'],
                            'isStream': False,
                            'title': track['name'],
                            'uri': f"https://open.spotify.com/track/{track['id']}"
                        },
                        requester=0
                    )
                )

            return tracks, playlist_info
        return [], None

    @staticmethod
    def get_track_id_from_url(url: str) -> Union[str, None]:
        """
        Get track id from url
        :param url: Spotify track url
        :return: Track id, None if not a track url
        """
        track_url_rx = re.compile(r'https?:\/\/open\.spotify\.com\/track\/(\w+)')

        match = track_url_rx.match(url)

        if match:
            return match.group(1)
        return None

    @staticmethod
    def get_playlist_id_from_url(url: str) -> Union[str, None]:
        """
        Get playlist id from url
        :param url: Spotify playlist url
        :return: Playlist id, None if not a playlist url
        """
        playlist_url_rx = re.compile(r'https?:\/\/open\.spotify\.com\/playlist\/(\w+)')

        match = playlist_url_rx.match(url)

        if match:
            return match.group(1)
        return None

    @staticmethod
    def get_album_id_from_url(url: str) -> Union[str, None]:
        """
        Get album id from url
        :param url: Spotify album url
        :return: Album id, None if not a album url
        """
        album_url_rx = re.compile(r'https?:\/\/open\.spotify\.com\/album\/(\w+)')

        match = album_url_rx.match(url)

        if match:
            return match.group(1)
        return None
