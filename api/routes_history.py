from typing import List
from fastapi import APIRouter, Query, HTTPException

from schemas.history import HistoryItem
from SpotiFLAC.core.session_memory import (
    get_url_history,
    clear_url_history,
    remove_url_from_history
)

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("", response_model=List[HistoryItem])
def get_history():
    """
    Retrieve URL download history.
    """
    try:
        return get_url_history()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("")
def clear_history():
    """
    Clear all URL history.
    """
    try:
        clear_url_history()
        return {"status": "success", "message": "History cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/item")
def remove_history_item(url: str = Query(...)):
    """
    Remove a specific URL from history.
    """
    try:
        remove_url_from_history(url)
        return {"status": "success", "message": f"URL removed from history"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
