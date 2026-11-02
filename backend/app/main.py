from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import get_settings, router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("windwise")

app = FastAPI(title="WindWise API", version="0.1.0",
              description="Wind forecast intelligence for day-ahead procurement decision support.")
app.add_middleware(CORSMiddleware, allow_origins=list(get_settings().cors_origins),
                   allow_methods=["GET"], allow_headers=["*"])
app.include_router(router)


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled error")  # details stay in logs, never in the response
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
