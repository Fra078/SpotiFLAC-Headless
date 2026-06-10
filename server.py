import logging
import json
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from api.routes_search import router as search_router
from api.routes_settings import router as settings_router
from api.routes_status import router as status_router
from api.routes_history import router as history_router
from api.routes_download import router as download_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SpotiFLAC.Server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Salva il file JSON di specifica OpenAPI all'avvio del server
    try:
        openapi_data = app.openapi()
        with open("openapi.json", "w", encoding="utf-8") as f:
            json.dump(openapi_data, f, indent=2)
        logger.info("OpenAPI schema successfully written to openapi.json")
    except Exception as e:
        logger.error(f"Failed to write OpenAPI schema: {e}")
    yield

app = FastAPI(
    title="SpotiFLAC Headless API",
    description="Application state and download endpoints",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(settings_router)
app.include_router(status_router)
app.include_router(history_router)
app.include_router(download_router)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Inietta manualmente la descrizione dell'endpoint WebSocket
    openapi_schema["paths"]["/api/download/ws"] = {
        "get": {
            "summary": "WebSocket Live Download Progress",
            "description": "Establishes a WebSocket connection to stream real-time download queue stats, progress, and speed updates.",
            "tags": ["Download"],
            "responses": {
                "101": {
                    "description": "Switching Protocols (Handshake successful)"
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)