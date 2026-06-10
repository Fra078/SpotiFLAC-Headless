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
        from SpotiFLAC.core.paths import get_default_download_dir
        target_dir = payload.output_dir or str(get_default_download_dir())
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
        return manager.get_stats()
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
    
    from SpotiFLAC.core.progress import DownloadBroadcaster, DownloadManager
    
    loop = asyncio.get_running_loop()
    q = asyncio.Queue()
    broadcaster = DownloadBroadcaster()
    broadcaster.subscribe(q, loop)
    
    # Send the initial status immediately upon connection
    try:
        manager = DownloadManager()
        await websocket.send_json(manager.get_stats())
    except Exception as e:
        logger.error(f"Error sending initial stats via WebSocket: {e}")
        broadcaster.unsubscribe(q)
        await websocket.close()
        return

    # Task to read from the websocket to detect client disconnection promptly
    async def receive_messages():
        try:
            async for _ in websocket.iter_text():
                pass
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    recv_task = asyncio.create_task(receive_messages())

    try:
        while not recv_task.done():
            get_task = asyncio.create_task(q.get())
            done, pending = await asyncio.wait(
                {get_task, recv_task},
                return_when=asyncio.FIRST_COMPLETED
            )
            
            if recv_task in done:
                get_task.cancel()
                break
                
            if get_task in done:
                stats = get_task.result()
                await websocket.send_json(stats)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        broadcaster.unsubscribe(q)
        recv_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass
        logger.info("WebSocket connection finalized and cleaned up")
