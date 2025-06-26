import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import aiohttp
import uvicorn
from disnake.abc import MISSING
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from lavalink import LoadType
from pydantic import BaseModel
from pylrc.classes import LyricLine

from lava.classes.player import LavaPlayer
from lava.utils import find_lyrics_within_range


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
    filters: List[str]


class QueueInfo(BaseModel):
    tracks: List[TrackInfo]
    total_count: int


class LyricLineInfo(BaseModel):
    text: str
    timestamp: float  # Time in seconds


class LyricsInfo(BaseModel):
    lyrics: List[LyricLineInfo]
    has_lyrics: bool


class PlayRequest(BaseModel):
    query: str
    index: Optional[int] = None
    shuffle: bool = False


class SkipRequest(BaseModel):
    target: Optional[int] = None
    move: bool = False


class VolumeRequest(BaseModel):
    volume: int


class FilterRequest(BaseModel):
    filter_name: str
    parameters: Optional[Dict[str, Any]] = None


class LavaAPI:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("lava.api")
        self.app = FastAPI(
            title="Lava Music Bot API",
            description="REST API for controlling the Lava music bot",
            version="1.0.0",
        )

        # Add CORS middleware to allow all origins
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allow all methods
            allow_headers=["*"],  # Allow all headers
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

            if not player.show_lyrics:
                return LyricsInfo(lyrics=[], has_lyrics=False)

            # Fetch lyrics if not cached
            if player.lyrics is None:
                await player.fetch_and_update_lyrics()

            if player.lyrics is None or player.lyrics == MISSING:
                return LyricsInfo(lyrics=[], has_lyrics=False)

            # Get all lyrics with timestamps
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

            if not player.show_lyrics:
                return LyricsInfo(lyrics=[], has_lyrics=False)

            # Fetch lyrics if not cached
            if player.lyrics is None:
                await player.fetch_and_update_lyrics()

            if player.lyrics == MISSING:
                return LyricsInfo(lyrics=[], has_lyrics=False)

            # Get lyrics within range of current position
            current_position_seconds = player.position / 1000
            lyrics_in_range = find_lyrics_within_range(
                player.lyrics, current_position_seconds, range_seconds
            )

            ranged_lyrics = [
                LyricLineInfo(text=line.text, timestamp=line.time)
                for line in lyrics_in_range
            ]

            return LyricsInfo(lyrics=ranged_lyrics, has_lyrics=True)

        @self.app.post("/player/{guild_id}/play")
        async def play_track(guild_id: int, request: PlayRequest):
            """Play a track or search query"""
            player = self._get_player(guild_id)

            # Search for tracks
            results = await self.bot.lavalink.get_local_tracks(request.query)

            if not results or not results.tracks:
                results = await player.node.get_tracks(request.query)

            if not results or not results.tracks:
                raise HTTPException(status_code=404, detail="No tracks found")

            # Find index position
            index = (
                request.index
                if request.index is not None
                else sum(1 for t in player.queue if t.requester)
            )

            added_tracks = []

            if results.load_type == LoadType.TRACK:
                player.add(requester=0, track=results.tracks[0], index=index)
                added_tracks.append(self._serialize_track(results.tracks[0]))

            elif results.load_type == LoadType.PLAYLIST:
                for iter_index, track in enumerate(results.tracks):
                    player.add(requester=0, track=track, index=index + iter_index)
                    added_tracks.append(self._serialize_track(track))

            # Start playing if not already
            if not player.is_playing:
                await player.play()

            # Set shuffle if requested
            player.set_shuffle(shuffle=request.shuffle)

            return {
                "message": "Track(s) added to queue",
                "tracks_added": len(added_tracks),
                "tracks": added_tracks,
            }

        @self.app.post("/player/{guild_id}/pause")
        async def pause_player(guild_id: int):
            """Pause the player"""
            player = self._get_player(guild_id)

            if not player.is_playing:
                raise HTTPException(status_code=400, detail="Nothing is playing")

            await player.set_pause(True)
            return {"message": "Player paused"}

        @self.app.post("/player/{guild_id}/resume")
        async def resume_player(guild_id: int):
            """Resume the player"""
            player = self._get_player(guild_id)

            if not player.paused:
                raise HTTPException(status_code=400, detail="Player is not paused")

            await player.set_pause(False)
            return {"message": "Player resumed"}

        @self.app.post("/player/{guild_id}/stop")
        async def stop_player(guild_id: int):
            """Stop the player and clear queue"""
            player = self._get_player(guild_id)

            await player.stop()
            player.queue.clear()

            # Disconnect from voice channel
            guild = self.bot.get_guild(guild_id)
            if guild and guild.voice_client:
                await guild.voice_client.disconnect(force=False)

            return {"message": "Player stopped and disconnected"}

        @self.app.post("/player/{guild_id}/skip")
        async def skip_track(guild_id: int, request: SkipRequest):
            """Skip current track or jump to specific track"""
            player = self._get_player(guild_id)

            if not player.is_playing:
                raise HTTPException(status_code=400, detail="Nothing is playing")

            if request.target:
                if len(player.queue) < request.target or request.target < 1:
                    raise HTTPException(status_code=400, detail="Invalid track number")

                if request.move:
                    player.queue.insert(0, player.queue.pop(request.target - 1))
                else:
                    player.queue = player.queue[request.target - 1 :]

            await player.skip()
            return {"message": "Track skipped"}

        @self.app.delete("/player/{guild_id}/queue/{track_index}")
        async def remove_track(guild_id: int, track_index: int):
            """Remove a track from the queue"""
            player = self._get_player(guild_id)

            if len(player.queue) < track_index or track_index < 1:
                raise HTTPException(status_code=400, detail="Invalid track number")

            removed_track = player.queue.pop(track_index - 1)
            return {
                "message": "Track removed",
                "removed_track": self._serialize_track(removed_track),
            }

        @self.app.delete("/player/{guild_id}/queue")
        async def clear_queue(guild_id: int):
            """Clear the entire queue"""
            player = self._get_player(guild_id)

            queue_size = len(player.queue)
            player.queue.clear()

            return {"message": f"Queue cleared, removed {queue_size} tracks"}

        @self.app.post("/player/{guild_id}/volume")
        async def set_volume(guild_id: int, request: VolumeRequest):
            """Set player volume"""
            player = self._get_player(guild_id)

            if request.volume < 0 or request.volume > 1000:
                raise HTTPException(
                    status_code=400, detail="Volume must be between 0 and 1000"
                )

            await player.set_volume(request.volume)
            return {"message": f"Volume set to {request.volume}"}

        @self.app.post("/player/{guild_id}/shuffle")
        async def toggle_shuffle(
            guild_id: int,
            enabled: bool = Query(..., description="Enable or disable shuffle"),
        ):
            """Toggle shuffle mode"""
            player = self._get_player(guild_id)

            player.set_shuffle(enabled)
            return {"message": f"Shuffle {'enabled' if enabled else 'disabled'}"}

        @self.app.post("/player/{guild_id}/loop")
        async def set_loop_mode(
            guild_id: int,
            mode: int = Query(..., description="Loop mode: 0=off, 1=track, 2=queue"),
        ):
            """Set loop mode"""
            player = self._get_player(guild_id)

            if mode not in [0, 1, 2]:
                raise HTTPException(
                    status_code=400, detail="Loop mode must be 0, 1, or 2"
                )

            player.set_loop(mode)

            mode_names = {0: "off", 1: "track", 2: "queue"}
            return {"message": f"Loop mode set to {mode_names[mode]}"}

        @self.app.post("/player/{guild_id}/autoplay")
        async def toggle_autoplay(
            guild_id: int,
            enabled: bool = Query(..., description="Enable or disable autoplay"),
        ):
            """Toggle autoplay mode"""
            player = self._get_player(guild_id)

            if enabled != player.autoplay:
                await player.toggle_autoplay()

            return {
                "message": f"Autoplay {'enabled' if player.autoplay else 'disabled'}"
            }

        @self.app.post("/player/{guild_id}/lyrics/toggle")
        async def toggle_lyrics(guild_id: int):
            """Toggle lyrics display"""
            player = self._get_player(guild_id)

            await player.toggle_lyrics()
            return {
                "message": f"Lyrics display {'enabled' if player.show_lyrics else 'disabled'}"
            }

        @self.app.post("/player/{guild_id}/filters")
        async def set_filter(guild_id: int, request: FilterRequest):
            """Set or remove audio filter"""
            from lava.cogs.commands import allowed_filters

            player = self._get_player(guild_id)

            if request.filter_name not in allowed_filters:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown filter. Available filters: {list(allowed_filters.keys())}",
                )

            if not request.parameters:
                # Remove filter
                await player.remove_filter(request.filter_name)
                return {"message": f"Filter {request.filter_name} removed"}

            # Set filter
            filter_class = allowed_filters[request.filter_name]
            audio_filter = player.get_filter(request.filter_name) or filter_class()

            try:
                audio_filter.update(**request.parameters)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid filter parameters: {str(e)}"
                )

            await player.set_filter(audio_filter)
            return {"message": f"Filter {request.filter_name} applied"}

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
            filters=list(player.filters.keys()),
        )

    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the FastAPI server"""
        config = uvicorn.Config(
            app=self.app, host=host, port=port, log_level="info", loop="asyncio"
        )
        server = uvicorn.Server(config)

        self.logger.info(f"Starting API server on {host}:{port}")
        await server.serve()


# Global API instance
api_instance: Optional[LavaAPI] = None


def setup_api(bot) -> LavaAPI:
    """Setup the API with the bot instance"""
    global api_instance
    api_instance = LavaAPI(bot)
    return api_instance


def get_api() -> Optional[LavaAPI]:
    """Get the current API instance"""
    return api_instance
