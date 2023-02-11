import json
import re
from os import getenv
from typing import Union, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from lavalink import Source, Client, LoadResult, LoadType, PlaylistInfo
from spotipy import Spotify, SpotifyOAuth
from youtube_dl import YoutubeDL
from youtube_dl.utils import UnsupportedError, DownloadError

from library.sources.track import SpotifyAudioTrack
from library.variables import Variables


class BaseSource:
    def __init__(self):
        """
        Inits the source
        :raise ValueError if the current state is not ok to use this source
        """
        self.priority: int = 0

    def check_query(self, query: str) -> bool:
        """
        Check if an url or keyword is supported by this source
        :return: Whether the query is supported
        """
        raise NotImplementedError

    async def load_item(self, client: Client, query: str) -> Optional[LoadResult]:
        """
        A function to load tracks
        :param client: Lavalink Client
        :param query: Query to search
        :return: The load result as LoadResult
        """
        raise NotImplementedError


class SpotifySource(BaseSource):
    def __init__(self):
        super().__init__()

        self.priority = 5

        spotify_client_id = getenv("SPOTIFY_CLIENT_ID")
        spotify_client_secret = getenv("SPOTIFY_CLIENT_SECRET")
        spotify_redirect_uri = getenv("SPOTIFY_REDIRECT_URI")

        if not (spotify_client_id and spotify_client_secret):
            raise ValueError(
                "One of SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URL enviorment variables is missing,"
                "Spotify links and autoplay will be disabled."
            )

        credentials = SpotifyOAuth(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri=spotify_redirect_uri,
            open_browser=False
        )

        Variables.SPOTIFY_CLIENT = Spotify(auth_manager=credentials)

        Variables.SPOTIFY_CLIENT.recommendations(seed_artists=["4NHQUGzhtTLFvgF5SZesLK"])

    def check_query(self, query: str) -> bool:
        spotify_url_rx = r'^(https://open\.spotify\.com/)(track|album|playlist)/([a-zA-Z0-9]+)(.*)$'

        if re.match(spotify_url_rx, query):
            return True

        return False

    async def load_item(self, client: Client, query: str):
        track = self.__load_track(query)

        if track:
            return LoadResult(LoadType.TRACK, [track], PlaylistInfo.none())

        playlist, playlist_info = self.__load_playlist(query)

        if playlist:
            return LoadResult(LoadType.PLAYLIST, playlist, playlist_info)

        album, playlist_info = self.__load_album(query)

        if album:
            return LoadResult(LoadType.PLAYLIST, album, playlist_info)

        return None

    def __load_track(self, url: str) -> Union[SpotifyAudioTrack, None]:
        """
        Get a track with given url from spotify, None if not found
        :param url: Spotify track url
        :return: SpotifyAudioTrack
        """
        track_id = self.__get_track_id_from_url(url)

        if not track_id:
            return None

        track = Variables.SPOTIFY_CLIENT.track(track_id)

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

    def __load_playlist(self, url: str) -> Tuple[list[SpotifyAudioTrack], Union[PlaylistInfo, None]]:
        """
        Get tracks in a playlist with given url from spotify, None if not found
        :param url: Spotify playlist url
        :return: list[SpotifyAudioTrack], PlaylistInfo
        """
        playlist_id = self.__get_playlist_id_from_url(url)

        if not playlist_id:
            return [], None

        playlist = Variables.SPOTIFY_CLIENT.playlist(playlist_id)

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

    def __load_album(self, url: str) -> Tuple[list[SpotifyAudioTrack], Union[PlaylistInfo, None]]:
        """
        Get tracks on an album with given url from spotify, None if not found
        :param url: Spotify album url
        :return: list[SpotifyAudioTrack], PlaylistInfo
        """
        album_id = self.__get_album_id_from_url(url)

        if not album_id:
            return [], None

        album = Variables.SPOTIFY_CLIENT.album(album_id)

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
    def __get_track_id_from_url(url: str) -> Union[str, None]:
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
    def __get_playlist_id_from_url(url: str) -> Union[str, None]:
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
    def __get_album_id_from_url(url: str) -> Union[str, None]:
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


class BilibiliSource(BaseSource):
    def __init__(self):
        super().__init__()

        self.priority = 5

    def check_query(self, query: str) -> bool:
        return query.startswith('https://www.bilibili.com/video/')

    async def load_item(self, client: Client, query: str) -> Optional[LoadResult]:
        audio_url, title = self.get_audio(query)

        track = (await client.get_tracks(audio_url, check_local=False)).tracks[0]

        track.title = title
        track.author = f'來自 [Bilibili]({query}) 的未知作者'

        return LoadResult(
            load_type=LoadType.TRACK,
            tracks=[track],
            playlist_info=None
        )

    def get_audio(self, url: str) -> Tuple[str, str]:
        """
        Gets audio URL from a Bilibili video URL

        Code referenced from https://www.bilibili.com/read/cv16789932
        :param url: Bilibili video URL
        :return: Tuple of audio URL and video title
        """
        video_html = requests.get(url)

        values = video_html.text

        text = BeautifulSoup(values, features='lxml')

        title = text.find('title').contents[0].replace(' ', ',').replace('/', ',')

        items = text.find_all('script')[2]

        items = items.contents[0].replace('window.__playinfo__=', '')

        obj = json.loads(items)

        audio_url = obj["data"]["dash"]["audio"][0]["baseUrl"]

        return audio_url, title


class YTDLSource(BaseSource):
    def __init__(self):
        super().__init__()

        self.priority = 0

        self.ytdl = YoutubeDL(
            {"format": "bestaudio"}
        )

    def check_query(self, query: str) -> bool:
        youtube_url_rx = r"^(https?://(www\.)?(youtube\.com|music\.youtube\.com)/(watch\?v=|playlist\?list=)([a-zA-Z0-9_-]+))"

        if re.match(youtube_url_rx, query):
            return False

        if not query.startswith("http://") or not query.startswith("https://"):
            return False

        return True

    async def load_item(self, client: Client, query: str) -> Optional[LoadResult]:
        try:
            url_info = self.ytdl.extract_info(query, download=False)

            if 'entries' in url_info:
                url_info = url_info['entries'][0]

        except (UnsupportedError, DownloadError):
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


class SourceManager(Source):
    def __init__(self):
        super().__init__(name='LavaSourceManager')

        self.sources: list[BaseSource] = []

        self.initial_sources()

    def initial_sources(self):
        for cls in BaseSource.__subclasses__():
            self.sources.append(cls())

        self.sources.sort(key=lambda x: x.priority, reverse=True)

    async def load_item(self, client: Client, query: str) -> Optional[LoadResult]:
        for source in self.sources:
            if not source.check_query(query):
                continue

            return await source.load_item(client, query)

        return None
