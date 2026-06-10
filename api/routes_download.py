import logging
import os
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect

from schemas.download import DownloadRequest, DownloadStatsSchema
from SpotiFLAC.downloader import SpotiflacDownloader, DownloadOptions
from SpotiFLAC.core.progress import DownloadManager

router = APIRouter(prefix="/api/download", tags=["Download"])
logger = logging.getLogger("SpotiFLAC.Server")

def run_download_background(payload: DownloadRequest):
    logger.info(f"Starting background download for URL: {payload.url}")
    try:
        target_dir = payload.output_dir or os.path.join(os.path.expanduser("~"), "Music", "SpotiFLAC")
        opts = DownloadOptions(
            output_dir=target_dir,
            services=payload.services,
            filename_format=payload.filename_format,
            use_track_numbers=payload.use_track_numbers,
            use_album_track_numbers=payload.use_album_track_numbers,
            use_artist_subfolders=payload.use_artist_subfolders,
            use_album_subfolders=payload.use_album_subfolders,
            first_artist_only=payload.first_artist_only,
            quality=payload.quality,
            allow_fallback=payload.allow_fallback,
            embed_lyrics=payload.embed_lyrics,
            lyrics_providers=payload.lyrics_providers,
            enrich_metadata=payload.enrich_metadata,
            enrich_providers=payload.enrich_providers,
            track_max_retries=payload.track_max_retries,
            post_download_action=payload.post_download_action,
            post_download_command=payload.post_download_command,
            qobuz_local_api_url=payload.qobuz_local_api_url,
            tidal_custom_api=payload.tidal_custom_api
        )
        downloader = SpotiflacDownloader(opts)
        downloader.run(payload.url)
        logger.info(f"Download successfully completed for URL: {payload.url}")
    except Exception as e:
        logger.error(f"Download failed for URL: {payload.url}. Error: {e}")

@router.post("")
def start_download(payload: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Queue a new download in the background.
    """
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    logger.info(f"Received download request for: {payload.url}")

    background_tasks.add_task(run_download_background, payload)

    return {"status": "queued", "message": "Download task initiated in the background."}

@router.get("/stats", response_model=DownloadStatsSchema)
def get_download_stats():
    """
    Get live progress, speeds, status of the current download queue, and list of latest completed files.
    """
    try:
        manager = DownloadManager()
        with manager._lock:
            queue_items = []
            completed_items = []
            
            for i in manager._queue:
                item_data = {
                    "id": i.id,
                    "track_name": i.track_name,
                    "artist_name": i.artist_name,
                    "album_name": i.album_name,
                    "spotify_id": i.spotify_id,
                    "status": i.status.value,
                    "progress": i.progress,
                    "total_size": i.total_size,
                    "speed": i.speed,
                    "file_path": i.file_path,
                    "end_time": i.end_time,
                    "error_message": i.error_message
                }
                queue_items.append(item_data)
                if i.status.value == "completed":
                    completed_items.append(item_data)
            
            # Sort completed items by end_time descending (latest completed first)
            completed_items.sort(key=lambda x: x["end_time"], reverse=True)
            latest_completed = completed_items[:20]
            
            # Recompute active downloaded bytes
            active_bytes = sum(item.progress for item in manager._queue if item.status.value == "downloading")
            
            queued = sum(1 for item in manager._queue if item.status.value == "queued")
            completed = len(completed_items)
            failed = sum(1 for item in manager._queue if item.status.value == "failed")
            skipped = sum(1 for item in manager._queue if item.status.value == "skipped")
            
            return {
                "is_downloading": manager.is_downloading,
                "current_speed": manager.current_speed,
                "total_downloaded": manager.total_downloaded + active_bytes,
                "queued": queued,
                "completed": completed,
                "failed": failed,
                "skipped": skipped,
                "downloads": queue_items,
                "queue": queue_items,
                "latest_completed": latest_completed
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
def reset_download_queue():
    """
    Reset the download manager queue and clear statistics.
    """
    try:
        manager = DownloadManager()
        manager.reset()
        return {"status": "success", "message": "Download queue reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws")
async def websocket_downloads(websocket: WebSocket):
    """
    WebSocket endpoint for real-time download queue monitoring and updates.
    """
    await websocket.accept()
    logger.info("WebSocket client connected to live download stats")
    try:
        last_stats = None
        while True:
            stats = get_download_stats()
            # Push updates only if the status changes (e.g. speed, progress, state changes)
            if stats != last_stats:
                await websocket.send_json(stats)
                last_stats = stats
            
            # Refresh rate is higher (500ms) when active downloading occurs
            sleep_time = 0.5 if stats.get("is_downloading") else 2.0
            await asyncio.sleep(sleep_time)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
