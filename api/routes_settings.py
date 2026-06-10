import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from schemas.settings import AppSettings
from schemas.settings import AudioQuality, ProviderService, LyricsProvider
from SpotiFLAC.core.profiles import (
    list_profiles,
    get_profile,
    save_profile,
    delete_profile
)

router = APIRouter(prefix="/api/settings", tags=["Settings"])

from SpotiFLAC.core.paths import get_cache_dir
SETTINGS_FILE = get_cache_dir() / "gui-settings.json"

@router.get("", response_model=AppSettings)
def get_global_settings():
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return AppSettings(**data)
        except Exception:
            pass
    return AppSettings()

@router.post("")
def update_global_settings(settings: AppSettings):
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            settings.model_dump_json(indent=2),
            encoding="utf-8"
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Profiles endpoints

@router.get("/profiles")
def get_all_profiles():
    return list_profiles()

@router.get("/profiles/{name}", response_model=AppSettings)
def get_single_profile(name: str):
    data = get_profile(name)
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return AppSettings(**data)

@router.post("/profiles/{name}")
def create_or_update_profile(name: str, settings: AppSettings):
    # exclude_unset prevents overwriting existing profile data with Pydantic defaults
    profile_data = settings.model_dump(exclude_unset=True)
    save_profile(name, profile_data)
    return {"status": "success", "profile": name}

@router.delete("/profiles/{name}")
def remove_profile(name: str):
    if delete_profile(name):
        return {"status": "deleted", "profile": name}
    raise HTTPException(status_code=404, detail="Profile not found")


@router.get("/options")
def get_available_options():
    """
    Fornisce al frontend tutte le opzioni valide lette direttamente
    dal Single Source of Truth (le Enum di Pydantic).
    """

    # Mappatura opzionale per dare al frontend delle etichette (label) "belle" da leggere
    quality_labels = {
        AudioQuality.LOSSLESS: "Lossless (FLAC)",
        AudioQuality.HIGH: "High (320 kbps)",
        AudioQuality.NORMAL: "Normal (128 kbps)"
    }

    service_labels = {
        ProviderService.TIDAL: "Tidal",
        ProviderService.QOBUZ: "Qobuz",
        ProviderService.DEEZER: "Deezer",
        ProviderService.APPLE: "Apple Music",
        ProviderService.SOUNDCLOUD: "SoundCloud",
        ProviderService.SPOTIFY: "Spotify"
    }

    return {
        "qualities": [
            {"id": q.value, "label": quality_labels.get(q, q.name)}
            for q in AudioQuality
        ],
        "services": [
            {"id": s.value, "label": service_labels.get(s, s.name.capitalize())}
            for s in ProviderService
        ],
        "lyrics_providers": [
            {"id": l.value, "label": l.name.capitalize()}
            for l in LyricsProvider
        ]
    }

