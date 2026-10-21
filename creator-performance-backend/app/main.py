"""Local Module C API. No database, queue, or external LLM is required to analyze an image."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.modules.module_c.config import get_settings
from app.modules.module_c.schemas import Category, Report, TitleLanguage
from app.modules.module_c.service import ThumbnailService

app = FastAPI(title="Sri Lankan Creator Assistant — Module C", version="0.1.0")


@lru_cache
def get_service():
    return ThumbnailService(get_settings())


@app.get("/health")
def health():
    return {"status": "ok", "service": "creator-performance-backend"}


@app.get("/api/module-c/status")
def module_c_status(service: Annotated[ThumbnailService, Depends(get_service)]):
    return service.status()


@app.post("/api/module-c/analyze", response_model=Report)
async def analyze(
    thumbnail: Annotated[UploadFile, File(description="JPEG, PNG, or WebP, up to 10 MiB")],
    title: Annotated[str, Form(min_length=1, max_length=500)],
    category: Annotated[Category, Form()],
    service: Annotated[ThumbnailService, Depends(get_service)],
    title_language: Annotated[TitleLanguage, Form()] = "unknown",
):
    settings = service.settings
    try:
        if thumbnail.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=415, detail="Use JPEG, PNG, or WebP.")
        if not title.strip():
            raise HTTPException(status_code=422, detail="Enter a non-empty title.")
        data = await thumbnail.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="Thumbnail exceeds the upload size limit.")
        try:
            report = await run_in_threadpool(service.analyze, data, title, category, title_language)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return await service.word_report(report)
    finally:
        await thumbnail.close()
