"""Local Module C API. No database, queue, or external LLM is required to analyze an image."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.demo import WEB_ROOT
from app.demo import router as demo_router
from app.modules.module_c.config import get_settings
from app.modules.module_c.schemas import Category, Report, TitleLanguage
from app.modules.module_c.service import ThumbnailService
from app.pp1 import analyze_a, analyze_b, combine, explain_c

app = FastAPI(title="Sri Lankan Creator Assistant — Module C", version="0.1.0")
app.mount("/static", StaticFiles(directory=WEB_ROOT), name="static")
app.include_router(demo_router)


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


@app.post("/api/pp1/analyze")
async def analyze_pp1(
    thumbnail: Annotated[UploadFile, File(description="JPEG, PNG, or WebP, up to 10 MiB")],
    title: Annotated[str, Form(min_length=1, max_length=500)],
    category: Annotated[Category, Form()],
    service: Annotated[ThumbnailService, Depends(get_service)],
    title_language: Annotated[TitleLanguage, Form()] = "unknown",
    description: Annotated[str, Form(max_length=3000)] = "",
    thumbnail_text: Annotated[str, Form(max_length=500)] = "",
    transcript: Annotated[str, Form(max_length=12000)] = "",
    transcript_complete: Annotated[bool, Form()] = False,
    consent_to_gemini: Annotated[bool, Form()] = False,
):
    """Independent module adapters; a single module failure leaves the others visible."""
    try:
        if thumbnail.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=415, detail="Use JPEG, PNG, or WebP.")
        if not title.strip():
            raise HTTPException(status_code=422, detail="Enter a non-empty title.")
        data = await thumbnail.read(service.settings.max_upload_bytes + 1)
        if len(data) > service.settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="Thumbnail exceeds the upload size limit.")
        try:
            # Validate the image before other modules; a broken upload is a request error.
            from app.modules.module_c.images import load_image
            await run_in_threadpool(load_image, data, service.settings.max_image_pixels)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        try:
            raw = await run_in_threadpool(service.analyze, data, title, category, title_language)
            try:
                explanation = await explain_c(raw, service.settings, consent_to_gemini)
            except Exception:  # noqa: BLE001 - optional explanation failure must preserve measurements.
                explanation = await explain_c(raw, service.settings, False)
                explanation["writer"]["reason"] = "explanation_unavailable"
            c = {"status": "completed", "maturity": "experimental", "raw": raw.model_dump(),
                 "measurements": raw.measurements, "findings": [f.model_dump() for f in raw.findings],
                 "explanations": explanation["items"], "explanation_writer": explanation["writer"],
                 "limitations": raw.limitations}
        except Exception:  # noqa: BLE001 - isolate independent module failure.
            c = {"status": "failed", "maturity": "experimental", "measurements": {}, "findings": [],
                 "explanations": [], "limitations": ["Thumbnail analysis failed for this request; other modules may still be available."]}
        try:
            b = await run_in_threadpool(analyze_b, title, category)
        except Exception:  # noqa: BLE001 - isolate independent module failure.
            b = {"status": "failed", "maturity": "experimental", "matches": [], "suggestions": [],
                 "limitations": ["Stored topic retrieval failed; no trend inference was made."]}
        try:
            a = await analyze_a(title, description, thumbnail_text, transcript,
                                transcript_complete, consent_to_gemini, service.settings)
        except Exception:  # noqa: BLE001 - isolate independent module failure.
            a = {"status": "failed", "maturity": "experimental", "observations": [],
                 "thumbnail_text_source": "user_supplied" if thumbnail_text else "unavailable",
                 "limitations": ["Transcript comparison failed; no integrity conclusion was made."]}
        return combine(a, b, c)
    finally:
        await thumbnail.close()
