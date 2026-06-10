import importlib.metadata
import re
from pathlib import Path
from typing import List
from fastapi import APIRouter, Query, HTTPException

from schemas.status import FfmpegStatus, NetworkStatus, HealthResultSchema, EndpointCheckResult
from SpotiFLAC.core.ffmpeg_check import check_ffmpeg
from SpotiFLAC.core.http import NetworkManager
from SpotiFLAC.core.health_check import run_health_check

router = APIRouter(prefix="/api/status", tags=["Status"])

def _get_app_version() -> str:
    try:
        return importlib.metadata.version("SpotiFLAC")
    except Exception:
        try:
            pyproj = Path(__file__).resolve().parents[2] / "pyproject.toml"
            text = pyproj.read_text(encoding="utf-8")
            m = re.search(r'^version\s*=\s*"([^\"]+)"', text, re.MULTILINE)
            if m:
                return m.group(1)
        except Exception:
            pass
    return "unknown"

APP_VERSION = _get_app_version()

@router.get("/version")
def get_version():
    return {"version": APP_VERSION}

@router.get("/ffmpeg", response_model=FfmpegStatus)
def get_ffmpeg_status():
    return check_ffmpeg()

@router.get("/network", response_model=NetworkStatus)
def get_network_status():
    try:
        client = NetworkManager.get_sync_client()
        resp = client.get("https://ipapi.co/json/", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "ip": data.get("ip", "Unavailable"),
                "country_name": data.get("country_name", "Unknown"),
                "country_code": data.get("country_code", "")
            }
    except Exception:
        pass
    return {"ip": "Unavailable", "country_name": "Unknown", "country_code": ""}

@router.get("/health", response_model=List[HealthResultSchema])
def get_health_status(services: List[str] = Query(["tidal", "qobuz", "deezer", "apple", "soundcloud", "spoti"])):
    """
    Runs health checks for the requested streaming service providers.
    """
    try:
        results = run_health_check(services)
        # Convert named tuples to dict representation suitable for pydantic parsing
        return [
            {
                "provider": r.provider,
                "url": r.url,
                "method": r.method,
                "ok": r.ok,
                "latency": r.latency,
                "detail": r.detail
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check_endpoint", response_model=EndpointCheckResult)
def check_custom_endpoint(url: str = Query(...)):
    """
    Performs a simple GET request validation on a custom API endpoint URL.
    """
    try:
        if not url or not url.strip():
            raise HTTPException(status_code=400, detail="URL must be a non-empty string")
        normalized = url.strip()
        if not normalized.lower().startswith('http'):
            raise HTTPException(status_code=400, detail="URL must start with http or https")
        
        client = NetworkManager.get_sync_client()
        resp = client.get(normalized, follow_redirects=True, timeout=10.0)
        return {
            'ok': 200 <= resp.status_code < 400,
            'status_code': resp.status_code,
            'url': str(resp.url),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
