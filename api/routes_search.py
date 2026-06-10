from fastapi import APIRouter, Query, HTTPException
from schemas.search import SearchResponse
from SpotiFLAC.providers.spotify_metadata import SpotifyMetadataClient

router = APIRouter()


@router.get("/api/search", response_model=SearchResponse)
def search_catalog(q: str = Query(...), limit: int = 50):
    try:
        client = SpotifyMetadataClient()
        results = client.search(q, limit=limit)

        out = {
            "tracks": [],
            "albums": [],
            "artists": [],
            "playlists": []
        }

        # Mapping attributes based on original legacy formats
        for t in results.get("tracks", [])[:limit]:
            out["tracks"].append({
                "id": getattr(t, 'id', ''),
                "title": getattr(t, 'title', ''),
                "artist": getattr(t, 'artists', ''),
                "album": getattr(t, 'album', ''),
                "duration_ms": getattr(t, 'duration_ms', 0),
                "cover": getattr(t, 'cover_url', ''),
                "external_url": getattr(t, 'external_url', ''),
                "preview_url": getattr(t, 'preview_url', ''),
                "playcount": getattr(t, 'plays', ''),
                "explicit": getattr(t, 'is_explicit', False),
                "isrc": getattr(t, 'isrc', ''),
            })

        for a in results.get("albums", [])[:limit]:
            out["albums"].append({
                "id": a.get("id", ""),
                "title": a.get("name", ""),
                "artist": a.get("artists", ""),
                "cover": a.get("cover_url", ""),
                "release_date": a.get("release_date", ""),
                "external_url": a.get("external_url", ""),
            })

        for art in results.get("artists", [])[:limit]:
            out["artists"].append({
                "id": art.get("id", ""),
                "title": art.get("name", ""),
                "cover": art.get("cover_url", ""),
                "external_url": art.get("external_url", ""),
            })

        for p in results.get("playlists", [])[:limit]:
            out["playlists"].append({
                "id": p.get("id", ""),
                "title": p.get("name", ""),
                "owner": p.get("owner", ""),
                "cover": p.get("cover_url", ""),
                "external_url": p.get("external_url", ""),
            })

        return out

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))