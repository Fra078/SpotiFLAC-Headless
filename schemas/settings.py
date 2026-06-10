from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import List, Optional


# --- 1. Definizione delle Enum ---

class AudioQuality(str, Enum):
    LOSSLESS = "LOSSLESS"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


class ProviderService(str, Enum):
    TIDAL = "tidal"
    QOBUZ = "qobuz"
    DEEZER = "deezer"
    APPLE = "apple"
    SOUNDCLOUD = "soundcloud"
    SPOTIFY = "spoti"


class LyricsProvider(str, Enum):
    SPOTIFY = "spotify"
    APPLE = "apple"
    MUSIXMATCH = "musixmatch"
    LRCLIB = "lrclib"
    AMAZON = "amazon"


# --- 2. Il DTO aggiornato ---

class AppSettings(BaseModel):
    # use_enum_values=True assicura che quando chiami .model_dump()
    # ti restituisca la stringa ("LOSSLESS") e non l'oggetto Enum
    model_config = ConfigDict(extra="allow", use_enum_values=True)

    output_dir: Optional[str] = None

    # Ora usiamo le Enum invece delle stringhe libere!
    quality: AudioQuality = AudioQuality.LOSSLESS
    services: List[ProviderService] = [
        ProviderService.TIDAL,
        ProviderService.QOBUZ,
        ProviderService.DEEZER
    ]
    lyrics_providers: List[LyricsProvider] = [
        LyricsProvider.SPOTIFY,
        LyricsProvider.APPLE,
        LyricsProvider.MUSIXMATCH,
        LyricsProvider.LRCLIB,
        LyricsProvider.AMAZON
    ]

    filename_format: str = "{title} - {artist}"
    use_track_numbers: bool = False
    use_album_track_numbers: bool = False
    use_artist_subfolders: bool = False
    use_album_subfolders: bool = False
    embed_lyrics: bool = True
    enrich_metadata: bool = True