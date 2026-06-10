from pydantic import BaseModel, Field
from typing import List, Optional

class DownloadRequest(BaseModel):
    url: str
    output_dir: Optional[str] = None
    quality: str = "LOSSLESS"
    services: List[str] = ["tidal", "qobuz", "deezer"]
    allow_fallback: bool = True
    filename_format: str = "{title} - {artist}"
    use_track_numbers: bool = False
    use_album_track_numbers: bool = False
    use_artist_subfolders: bool = False
    use_album_subfolders: bool = False
    first_artist_only: bool = False
    embed_lyrics: bool = True
    lyrics_providers: List[str] = ["spotify", "apple", "musixmatch", "lrclib", "amazon"]
    enrich_metadata: bool = True
    enrich_providers: List[str] = ["deezer", "apple", "qobuz", "tidal", "soundcloud"]
    track_max_retries: int = 0
    post_download_action: str = "none"
    post_download_command: str = ""
    qobuz_local_api_url: Optional[str] = None
    tidal_custom_api: Optional[str] = None

class QueueItemSchema(BaseModel):
    id: str
    track_name: str
    artist_name: str
    album_name: str
    spotify_id: str
    status: str
    progress: float
    total_size: float
    speed: float
    file_path: Optional[str] = ""
    end_time: Optional[float] = 0.0
    error_message: Optional[str] = ""

class DownloadStatsSchema(BaseModel):
    is_downloading: bool
    current_speed: float
    total_downloaded: float
    queued: int
    completed: int
    failed: int
    skipped: int
    downloads: List[QueueItemSchema] = Field(json_schema_extra={"default": []})
    queue: List[QueueItemSchema]
    latest_completed: List[QueueItemSchema] = []
