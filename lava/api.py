import logging
from typing import List, Optional

import aiohttp
import uvicorn
from disnake.abc import MISSING
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from lava.classes.player import LavaPlayer
from lava.utils import find_lyrics_within_range


class TimescaleFilter(BaseModel):
    speed: Optional[float] = None
    pitch: Optional[float] = None
    rate: Optional[float] = None


class TremoloFilter(BaseModel):
    frequency: Optional[float] = None
    depth: Optional[float] = None


class VibratoFilter(BaseModel):
    frequency: Optional[float] = None
    depth: Optional[float] = None


class RotationFilter(BaseModel):
    rotation_hz: Optional[float] = None


class LowPassFilter(BaseModel):
    smoothing: Optional[float] = None


class EqualizerFilter(BaseModel):
    bands: Optional[List[List[float]]] = None


class FilterInfo(BaseModel):
    timescale: Optional[TimescaleFilter] = None
    tremolo: Optional[TremoloFilter] = None
    vibrato: Optional[VibratoFilter] = None
    rotation: Optional[RotationFilter] = None
    lowpass: Optional[LowPassFilter] = None
    equalizer: Optional[EqualizerFilter] = None


class TrackInfo(BaseModel):
    title: str
    author: str
    duration: int
    position: int
    uri: str
    artwork_url: Optional[str] = None
    requester: int


class PlayerState(BaseModel):
    is_playing: bool
    is_paused: bool
    is_connected: bool
    current_track: Optional[TrackInfo] = None
    volume: int
    loop_mode: int
    shuffle: bool
    autoplay: bool
    position: int
    filters: FilterInfo
    lyrics_loaded: bool


class QueueInfo(BaseModel):
    tracks: List[TrackInfo]
    total_count: int


class LyricLineInfo(BaseModel):
    text: str
    timestamp: float


class LyricsInfo(BaseModel):
    lyrics: List[LyricLineInfo]
    has_lyrics: bool


class LavaAPI:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("lava.api")
        self.app = FastAPI(
            title="Lava Music Bot API",
            description="REST API for controlling the Lava music bot",
            version="1.0.0",
        )

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()

    def _setup_routes(self):
        """Setup all API routes"""

        @self.app.get("/")
        async def root():
            return {"message": "Lava Music Bot API", "version": "1.0.0"}

        @self.app.get("/guilds")
        async def get_guilds():
            """Get list of guilds the bot is in"""
            guilds = []
            for guild in self.bot.guilds:
                guilds.append(
                    {
                        "id": guild.id,
                        "name": guild.name,
                        "member_count": guild.member_count,
                    }
                )
            return {"guilds": guilds}

        @self.app.get("/player/{guild_id}", response_model=PlayerState)
        async def get_player_state(guild_id: int):
            """Get current player state for a guild"""
            player = self._get_player(guild_id)

            return self._serialize_player_state(player)

        @self.app.get(
            "/player/{guild_id}/nowplaying", response_model=Optional[TrackInfo]
        )
        async def get_now_playing(guild_id: int):
            """Get currently playing track"""
            player = self._get_player(guild_id)
            if not player.current:
                return None

            return self._serialize_player_state(player).current_track

        @self.app.get("/player/{guild_id}/artwork")
        async def get_current_artwork(guild_id: int):
            """Get artwork image for currently playing track"""
            player = self._get_player(guild_id)
            self.bot.logger.info("Getting artwork for %s", player.current)

            if not player.current:
                raise HTTPException(
                    status_code=404, detail="No track currently playing"
                )

            artwork_url = getattr(player.current, "artwork_url", None)
            if not artwork_url:
                raise HTTPException(
                    status_code=404, detail="No artwork available for current track"
                )

            return await self._fetch_artwork(artwork_url)

        @self.app.get("/player/{guild_id}/queue", response_model=QueueInfo)
        async def get_queue(
            guild_id: int,
            limit: int = Query(50, description="Maximum number of tracks to return"),
        ):
            """Get player queue"""
            player = self._get_player(guild_id)
            tracks = [self._serialize_track(track) for track in player.queue[:limit]]
            return QueueInfo(tracks=tracks, total_count=len(player.queue))

        @self.app.get("/player/{guild_id}/lyrics", response_model=LyricsInfo)
        async def get_lyrics(guild_id: int):
            """Get lyrics for currently playing track"""
            player = self._get_player(guild_id)

            if not player.current:
                raise HTTPException(
                    status_code=404, detail="No track currently playing"
                )

            if player.lyrics is None:
                await player.fetch_and_update_lyrics()

            if player.lyrics is None or player.lyrics == MISSING:
                return LyricsInfo(lyrics=[], has_lyrics=False)

            all_lyrics = [
                LyricLineInfo(text=line.text, timestamp=line.time)
                for line in player.lyrics
            ]

            return LyricsInfo(lyrics=all_lyrics, has_lyrics=True)

        @self.app.get("/player/{guild_id}/lyrics/current", response_model=LyricsInfo)
        async def get_current_lyrics(
            guild_id: int,
            range_seconds: float = Query(
                5.0, description="Time range in seconds around current position"
            ),
        ):
            """Get lyrics for currently playing track within time range of current position"""
            player = self._get_player(guild_id)

            if not player.current:
                raise HTTPException(
                    status_code=404, detail="No track currently playing"
                )

            if player.lyrics is None:
                await player.fetch_and_update_lyrics()

            if player.lyrics is None or player.lyrics == MISSING:
                return LyricsInfo(lyrics=[], has_lyrics=False)

            current_position_seconds = player.position / 1000
            lyrics_in_range = find_lyrics_within_range(
                player.lyrics, current_position_seconds, range_seconds
            )

            ranged_lyrics = [
                LyricLineInfo(text=line.text, timestamp=line.time)
                for line in lyrics_in_range
            ]

            return LyricsInfo(lyrics=ranged_lyrics, has_lyrics=True)

        @self.app.get("/player/{guild_id}/filters")
        async def get_filters(guild_id: int):
            """Get currently active filters"""
            player = self._get_player(guild_id)

            return {"filters": list(player.filters.keys())}

    async def _fetch_artwork(self, artwork_url: str) -> Response:
        """Fetch artwork image from URL and return as Response"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(artwork_url) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=404,
                            detail="Artwork not found or unavailable",
                        )

                    image_data = await response.read()
                    content_type = response.headers.get("content-type", "image/jpeg")

                    return Response(
                        content=image_data,
                        media_type=content_type,
                        headers={
                            "Cache-Control": "public, max-age=3600",
                            "Content-Length": str(len(image_data)),
                        },
                    )

        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=503, detail=f"Failed to fetch artwork: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal error while fetching artwork: {str(e)}",
            )

    def _get_player(self, guild_id: int) -> LavaPlayer:
        """Get player for guild, raise HTTP exception if not found"""
        if not self.bot.is_ready():
            raise HTTPException(status_code=503, detail="Bot is not ready")

        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise HTTPException(status_code=404, detail="Guild not found")

        player = self.bot.lavalink.player_manager.get(guild_id)
        if not player:
            raise HTTPException(
                status_code=404, detail="No player found for this guild"
            )

        return player

    def _serialize_filters(self, player_filters) -> FilterInfo:
        """Convert player filters to FilterInfo model"""
        filter_data = {}

        for name, filter_obj in player_filters.items():
            if name == "timescale":
                filter_data["timescale"] = TimescaleFilter(
                    speed=getattr(filter_obj, "speed", None),
                    pitch=getattr(filter_obj, "pitch", None),
                    rate=getattr(filter_obj, "rate", None),
                )
            elif name == "tremolo":
                filter_data["tremolo"] = TremoloFilter(
                    frequency=getattr(filter_obj, "frequency", None),
                    depth=getattr(filter_obj, "depth", None),
                )
            elif name == "vibrato":
                filter_data["vibrato"] = VibratoFilter(
                    frequency=getattr(filter_obj, "frequency", None),
                    depth=getattr(filter_obj, "depth", None),
                )
            elif name == "rotation":
                filter_data["rotation"] = RotationFilter(
                    rotation_hz=getattr(filter_obj, "rotation_hz", None)
                )
            elif name == "lowpass":
                filter_data["lowpass"] = LowPassFilter(
                    smoothing=getattr(filter_obj, "smoothing", None)
                )
            elif name == "equalizer":
                bands = getattr(filter_obj, "bands", None)
                if bands:
                    bands = [[band.band, band.gain] for band in bands]
                filter_data["equalizer"] = EqualizerFilter(bands=bands)

        return FilterInfo(**filter_data)

    def _serialize_track(self, track) -> TrackInfo:
        """Convert lavalink track to TrackInfo model"""
        return TrackInfo(
            title=track.title,
            author=track.author,
            duration=track.duration,
            position=track.position if hasattr(track, "position") else 0,
            uri=track.uri,
            artwork_url=getattr(track, "artwork_url", None),
            requester=track.requester,
        )

    def _serialize_player_state(self, player: LavaPlayer) -> PlayerState:
        """Convert player to PlayerState model"""
        current_track = None

        if player.current:
            current_track = self._serialize_track(player.current)
            current_track.position = player.position

        return PlayerState(
            is_playing=player.is_playing,
            is_paused=player.paused,
            is_connected=player.is_connected,
            current_track=current_track,
            volume=player.volume,
            loop_mode=player.loop,
            shuffle=player.shuffle,
            autoplay=player.autoplay,
            position=player.position,
            filters=self._serialize_filters(player.filters),
            lyrics_loaded=player.lyrics is not None,
        )

    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the FastAPI server"""
        config = uvicorn.Config(
            app=self.app, host=host, port=port, log_level="info", loop="asyncio"
        )
        server = uvicorn.Server(config)

        self.logger.info(f"Starting API server on {host}:{port}")
        await server.serve()


api_instance: Optional[LavaAPI] = None


def setup_api(bot) -> LavaAPI:
    """Setup the API with the bot instance"""
    global api_instance
    api_instance = LavaAPI(bot)
    return api_instance


def get_api() -> Optional[LavaAPI]:
    """Get the current API instance"""
    return api_instance
