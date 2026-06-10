from pydantic import BaseModel
from typing import List, Optional

class BaseItem(BaseModel):
    id: str
    title: str
    cover: Optional[str] = ""
    external_url: Optional[str] = ""
    provider: str = "spotify"

class TrackResponse(BaseItem):
    type: str = "track"
    artist: str
    album: str
    duration_ms: int
    preview_url: Optional[str] = ""
    playcount: Optional[str] = ""
    explicit: bool = False
    isrc: str = ""

class AlbumResponse(BaseItem):
    type: str = "album"
    artist: str
    release_date: str = ""

class ArtistResponse(BaseItem):
    type: str = "artist"

class PlaylistResponse(BaseItem):
    type: str = "playlist"
    owner: str = ""

class SearchResponse(BaseModel):
    tracks: List[TrackResponse]
    albums: List[AlbumResponse]
    artists: List[ArtistResponse]
    playlists: List[PlaylistResponse]