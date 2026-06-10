from pydantic import BaseModel
from typing import List, Optional

class FfmpegStatus(BaseModel):
    available: bool
    version: str
    error: str

class NetworkStatus(BaseModel):
    ip: str
    country_name: str
    country_code: str

class HealthResultSchema(BaseModel):
    provider: str
    url: str
    method: str
    ok: bool
    latency: float
    detail: str

class EndpointCheckResult(BaseModel):
    ok: bool
    status_code: int
    url: str
