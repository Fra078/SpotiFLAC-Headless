import os
from pathlib import Path

def get_cache_dir() -> Path:
    """
    Ritorna la cartella cache dell'applicazione.
    Usa SPOTIFLAC_CACHE_DIR o XDG_CACHE_HOME se presenti, altrimenti ~/.cache/spotiflac.
    """
    custom = os.getenv("SPOTIFLAC_CACHE_DIR")
    if custom:
        return Path(custom)
    
    xdg = os.getenv("XDG_CACHE_HOME")
    if xdg:
        return Path(xdg) / "spotiflac"
        
    return Path.home() / ".cache" / "spotiflac"

def get_default_download_dir() -> Path:
    """
    Ritorna la cartella di download predefinita.
    Usa SPOTIFLAC_DOWNLOAD_DIR se presente, altrimenti /downloads (se esiste in Docker),
    oppure ~/Music/SpotiFLAC come fallback locale.
    """
    custom = os.getenv("SPOTIFLAC_DOWNLOAD_DIR")
    if custom:
        return Path(custom)
        
    if os.path.exists("/downloads"):
        return Path("/downloads")
        
    return Path(os.path.expanduser("~")) / "Music" / "SpotiFLAC"
