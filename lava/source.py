import re
from logging import getLogger
from os import getenv
from typing import Union, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from lavalink import Source, Client, LoadResult, LoadType, PlaylistInfo, DeferredAudioTrack
from spotipy import Spotify, SpotifyClientCredentials
from yt_dlp import YoutubeDL
from yt_dlp.utils import UnsupportedError, DownloadError

from lava.errors import LoadError


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


class SpotifyAudioTrack(DeferredAudioTrack):
    def __init__(self, track, requester, **extra):
        super().__init__(track, requester, **extra)

        self.track = None

    async def load(self, client):  # skipcq: PYL-W0201
        getLogger('lava.sources').info("Loading spotify track %s...", self.title)

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


class SpotifySource(BaseSource):
    def __init__(self):
        super().__init__()

        self.priority = 5

        spotify_client_id = getenv("SPOTIFY_CLIENT_ID")
        spotify_client_secret = getenv("SPOTIFY_CLIENT_SECRET")

        credentials = SpotifyClientCredentials(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret
        )

        self.spotify_client = Spotify(auth_manager=credentials)

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

        track = self.spotify_client.track(track_id)

        if track:
            return SpotifyAudioTrack(
                {
                    'identifier': track['id'],
                    'isSeekable': True,
                    'author': ', '.join([artist['name'] for artist in track['artists']]),
                    'length': track['duration_ms'],
                    'isStream': False,
                    'title': track['name'],
                    'uri': f"https://open.spotify.com/track/{track['id']}",
                    'artworkUrl': track['album']['images'][0]['url']
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

        playlist = self.spotify_client.playlist(playlist_id)

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
                            'uri': f"https://open.spotify.com/track/{track['track']['id']}",
                            'artworkUrl': track['track']['images'][0]['url']
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

        album = self.spotify_client.album(album_id)

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
                            'uri': f"https://open.spotify.com/track/{track['id']}",
                            'artworkUrl': album['images'][0]['url']
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
        return query.startswith('https://www.bilibili.com/video/') or query.startswith('https://b23.tv/')

    async def load_item(self, client: Client, query: str) -> Optional[LoadResult]:
        audio_url, title, author = self.get_audio(query)

        track = (await client.get_tracks(audio_url, check_local=False)).tracks[0]

        track.title = title
        track.author = f'{author} / [Bilibili]({query})'

        return LoadResult(
            load_type=LoadType.TRACK,
            tracks=[track],
            playlist_info=None
        )

    @staticmethod
    def get_video_info(bvid: str) -> Tuple[str, str]:
        """
        Gets video info from a Bilibili video bvid

        :param bvid: Bilibili video bvid
        :return: Tuple of video cid, video session
        """
        headers = {
            'referer': 'https://www.bilibili.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
        }
        video_index_url = f"https://www.bilibili.com/video/{bvid}"
        resp = requests.get(video_index_url, headers=headers).text
        cid = re.findall('"cid":(\\d+),', resp)[0]
        session = re.findall('"session":"(.*?)"', resp)[0]
        return cid, session

    def get_audio_url(self, url: str):
        """
        Gets audio URL from a Bilibili video URL

        :param url: Bilibili video URL
        :return: audio URL
        """
        headers = {
            'referer': 'https://www.bilibili.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
        }

        bvid = re.search(r"/video/([^/?]+)", url).group(1)

        cid, session = self.get_video_info(bvid)

        play_url = 'https://api.bilibili.com/x/player/playurl'

        params = {
            'cid': cid,
            'qn': '2',
            'type': '',
            'otype': 'json',
            'fourk': '1',
            'bvid': bvid,
            'fnver': '0',
            'fnval': '976',
            'session': session,
        }

        for _ in range(20):
            json_data = requests.get(url=play_url, params=params, headers=headers).json()
            audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
            if audio_url.startswith("https://upos-hz-mirrorakam.akamaized.net/"):
                return audio_url

    def get_audio(self, url: str) -> Tuple[str, str, str]:
        """
        Gets audio from a Bilibili video URL

        :param url: Bilibili video URL
        :return: Tuple of audio URL, video title, video author.
        """
        headers = {
            'Connection': 'Keep-Alive',
            'Accept-Language': 'en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
            'Accept': 'text/html, application/xhtml+xml, */*',
            'referer': 'https://www.bilibili.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
        }

        video_html = requests.get(url, headers=headers)

        values = video_html.text

        text = BeautifulSoup(values, features='html.parser')

        title = text.find('title').contents[0].replace(' ', ',').replace('/', ',')

        author = text.select_one('div.up-detail-top a').text.replace("\n", "")

        audio_url = self.get_audio_url(url)

        return audio_url, title, author


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

        if not ((query.startswith("http://")) or (query.startswith("https://"))):
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
        track.author = f"Unknown / [{match.group(1)}]({match.group(0)})"

        return LoadResult(
            load_type=LoadType.TRACK,
            tracks=[track],
            playlist_info=PlaylistInfo.none()
        )


class SourceManager(Source):
    def __init__(self):
        super().__init__(name='LavaSourceManager')

        self.sources: list[BaseSource] = []

        self.logger = getLogger('lava.sources')

        self.initial_sources()

    def initial_sources(self):
        self.logger.info('Initializing sources...')

        for cls in BaseSource.__subclasses__():
            self.logger.debug(f'Initializing {cls.__name__}...')

            self.sources.append(cls())

        self.sources.sort(key=lambda x: x.priority, reverse=True)

    async def load_item(self, client: Client, query: str) -> Optional[LoadResult]:
        self.logger.info("Received query: %s, checking in sources...", query)

        for source in self.sources:
            self.logger.debug("Checking source for query %s: %s", query, source.__class__.__name__)

            if not source.check_query(query):
                self.logger.debug("Source %s does not match query %s, skipping...", source.__class__.__name__, query)

                continue

            self.logger.info("Source %s matched query %s, loading...", source.__class__.__name__, query)

            return await source.load_item(client, query)

        self.logger.info("No sources matched query %s, returning None", query)
        return None
