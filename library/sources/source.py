import re
from typing import Union, Tuple, Optional

from lavalink import Source, Client, LoadResult, LoadType, PlaylistInfo
from spotipy import Spotify
from youtube_dl import YoutubeDL
from youtube_dl.utils import UnsupportedError

from library.sources.track import SpotifyAudioTrack


class YTDLSource(Source):
    def __init__(self):
        super().__init__(name='ytdl')

        self.ytdl = YoutubeDL()

    async def load_item(self, client: Client, query: str) -> Optional[LoadResult]:
        if 'youtube' in query or 'youtu.be' in query:  # Lavalink node will handle that, so skip
            return None

        try:
            url_info = self.ytdl.extract_info(query, download=False)

            if 'entries' in url_info:
                url_info = url_info['entries'][0]

        except UnsupportedError:
            return None

        try:
            track = (await client.get_tracks(url_info['formats'][-1]['url'])).tracks[0]

        except IndexError:
            return None

        match = re.match(r'^(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n]+)', url_info['webpage_url'])

        track.title = url_info['title']
        track.author = f"來自 [{match.group(1)}]({match.group(0)}) 的未知作者"

        return LoadResult(
            load_type=LoadType.TRACK,
            tracks=[track],
            playlist_info=PlaylistInfo.none()
        )


class SpotifySource(Source):
    def __init__(self, spotify: Spotify):
        super().__init__(name='spotify')  # Initialising our custom source with the name 'custom'.

        self.spotify = spotify

    async def load_item(self, client: Client, query: str):
        track = self.load_track(query)

        if track:
            return LoadResult(LoadType.TRACK, [track], PlaylistInfo.none())

        playlist, playlist_info = self.load_playlist(query)

        if playlist:
            return LoadResult(LoadType.PLAYLIST, playlist, playlist_info)

        album, playlist_info = self.load_album(query)

        if album:
            return LoadResult(LoadType.PLAYLIST, album, playlist_info)

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
