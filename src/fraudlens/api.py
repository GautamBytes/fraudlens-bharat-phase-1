"""HTTP application boundary for FraudLens Bharat."""

from contextlib import asynccontextmanager
from typing import AsyncIterable, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.concurrency import run_in_threadpool

from fraudlens.analysis_service import (
    AnalysisInput,
    CaseStore,
    DatabaseCaseStore,
    build_complaint_draft,
    create_analysis_service,
    resolve_predictor,
)
from fraudlens.image_analysis import ImageAnalysisInput, ImageAnalysisService
from fraudlens.graph_analysis import EntityGraphResult
from fraudlens.ocr import (
    ImageTooLargeError,
    InvalidImageError,
    NoTextDetectedError,
    OcrError,
    OcrService,
    OcrTimeoutError,
    OcrUnavailableError,
)
from fraudlens import __version__
from fraudlens.observability import configure_request_logging, write_request_log
from fraudlens.prediction import Predictor, PredictorRegistry
from fraudlens.schemas import AnalysisResult, AnalyzeRequest
from fraudlens.settings import Settings


async def _read_limited_image_stream(
    stream: AsyncIterable[bytes],
    max_bytes: int,
) -> bytes:
    image_bytes = bytearray()
    async for chunk in stream:
        remaining = max_bytes + 1 - len(image_bytes)
        if remaining > 0:
            image_bytes.extend(chunk[:remaining])
        if len(image_bytes) > max_bytes or len(chunk) > remaining:
            raise ImageTooLargeError("Image encoded size exceeds the configured limit")
    return bytes(image_bytes)


def create_app(
    settings: Optional[Settings] = None,
    predictor: Optional[Predictor] = None,
    store: Optional[CaseStore] = None,
    predictor_registry: Optional[PredictorRegistry] = None,
    ocr_service: Optional[OcrService] = None,
) -> FastAPI:
    """Build the API with explicit runtime dependencies where needed."""

    resolved_settings = settings or Settings.from_env()
    try:
        resolved_predictor = resolve_predictor(
            resolved_settings,
            predictor=predictor,
            predictor_registry=predictor_registry,
        )
    except ValueError:
        raise ValueError("Application configuration is invalid") from None
    resolved_store = (
        store
        if store is not None
        else DatabaseCaseStore(
            resolved_settings.database_path,
            hmac_secret=resolved_settings.hmac_secret,
            retention_days=resolved_settings.retention_days,
        )
    )
    resolved_ocr_service = ocr_service if ocr_service is not None else OcrService()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        configure_request_logging()
        application.state.settings = resolved_settings
        application.state.case_store = resolved_store
        initializer = getattr(resolved_store, "initialize", None)
        if initializer is not None:
            try:
                initializer()
            except Exception:
                raise RuntimeError("Case storage initialization failed") from None
        analysis_service = create_analysis_service(
            settings=resolved_settings,
            predictor=resolved_predictor,
            store=resolved_store,
        )
        application.state.analysis_service = analysis_service
        application.state.ocr_service = resolved_ocr_service
        application.state.image_analysis_service = ImageAnalysisService(
            resolved_ocr_service,
            analysis_service,
        )
        yield

    application = FastAPI(
        title="FraudLens Bharat API",
        description="Privacy-conscious cyber-fraud triage API for Hinglish, Hindi, and English messages.",
        version=__version__,
        lifespan=lifespan,
    )
    if resolved_settings.allowed_hosts:
        application.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=list(resolved_settings.allowed_hosts),
        )

    @application.middleware("http")
    async def observe_and_secure_api_response(request: Request, call_next):
        request_id = uuid4().hex
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            write_request_log(
                request_id=request_id,
                method=request.method,
                route=_route_template(request),
                status_code=status_code,
            )
            raise
        write_request_log(
            request_id=request_id,
            method=request.method,
            route=_route_template(request),
            status_code=status_code,
        )
        response.headers["X-Request-ID"] = request_id
        if response.headers.get("content-type", "").startswith("application/json"):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "fraudlens-bharat", "version": __version__}

    @application.get("/ready")
    def ready(request: Request) -> dict:
        try:
            request.app.state.case_store.healthcheck()
        except Exception:
            raise HTTPException(status_code=503, detail="Service not ready") from None
        return {"status": "ready", "service": "fraudlens-bharat", "version": __version__}

    @application.post("/analyze", response_model=AnalysisResult)
    def analyze(analysis_request: AnalyzeRequest, request: Request) -> AnalysisResult:
        store_case = analysis_request.store_case
        if store_case is None:
            store_case = request.app.state.settings.store_cases_by_default
        try:
            return request.app.state.analysis_service.analyze(
                AnalysisInput(
                    text=analysis_request.text,
                    user_notes=analysis_request.user_notes,
                    store_case=store_case,
                )
            )
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error") from None

    @application.post("/analyze-image", response_model=AnalysisResult)
    async def analyze_image(
        request: Request,
        store_case: Optional[bool] = Query(default=None),
        user_notes: Optional[str] = Query(default=None, max_length=2_000),
    ) -> AnalysisResult:
        media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if media_type not in {"image/png", "image/jpeg"}:
            raise HTTPException(status_code=415, detail="Unsupported image media type")

        content_encoding = request.headers.get("content-encoding")
        if content_encoding is not None and content_encoding.strip().lower() != "identity":
            raise HTTPException(status_code=415, detail="Unsupported content encoding")

        max_bytes = request.app.state.ocr_service.policy.max_bytes
        content_length = request.headers.get("content-length")
        if content_length is not None:
            if not content_length.isascii() or not content_length.isdigit():
                raise HTTPException(status_code=400, detail="Invalid Content-Length")
            try:
                parsed_content_length = int(content_length, 10)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid Content-Length") from None
            if parsed_content_length > max_bytes:
                raise HTTPException(status_code=413, detail="Image upload is too large")

        try:
            image_bytes = await _read_limited_image_stream(request.stream(), max_bytes)
            resolved_store_case = store_case
            if resolved_store_case is None:
                resolved_store_case = request.app.state.settings.store_cases_by_default
            return await run_in_threadpool(
                request.app.state.image_analysis_service.analyze,
                ImageAnalysisInput(
                    image_bytes=image_bytes,
                    media_type=media_type,
                    user_notes=user_notes,
                    store_case=resolved_store_case,
                )
            )
        except ImageTooLargeError:
            raise HTTPException(status_code=413, detail="Image upload is too large") from None
        except OcrUnavailableError:
            raise HTTPException(status_code=503, detail="OCR service unavailable") from None
        except OcrTimeoutError:
            raise HTTPException(status_code=504, detail="OCR service timed out") from None
        except (InvalidImageError, NoTextDetectedError, OcrError):
            raise HTTPException(status_code=422, detail="Image could not be analyzed") from None
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error") from None

    @application.get("/cases")
    def cases(request: Request, limit: int = Query(default=20, ge=1, le=100)) -> list[dict]:
        try:
            return request.app.state.case_store.list_cases(limit=limit)
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error") from None

    @application.delete("/cases")
    def clear_case_history(
        request: Request,
        confirm: bool = Query(default=False),
    ) -> dict:
        if not confirm:
            raise HTTPException(status_code=400, detail="Explicit confirmation is required")
        try:
            deleted_count = request.app.state.case_store.clear()
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error") from None
        return {"deleted_count": deleted_count}

    @application.get("/graph")
    def entity_graph(
        request: Request,
        minimum_case_count: int = Query(default=2, ge=2, le=20),
        case_limit: int = Query(default=100, ge=1, le=100),
    ) -> EntityGraphResult:
        try:
            return request.app.state.case_store.entity_graph(
                minimum_case_count=minimum_case_count,
                case_limit=case_limit,
                max_edges=1_000,
            )
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error") from None

    @application.get("/cases/{case_id}")
    def case_detail(case_id: str, request: Request) -> dict:
        try:
            result = request.app.state.case_store.get_case(case_id)
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error") from None
        if result is None:
            raise HTTPException(status_code=404, detail="Case not found")
        return result

    @application.delete("/cases/{case_id}")
    def delete_case(
        case_id: str,
        request: Request,
        confirm: bool = Query(default=False),
    ) -> dict:
        if not confirm:
            raise HTTPException(status_code=400, detail="Explicit confirmation is required")
        try:
            deleted = request.app.state.case_store.delete(case_id)
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error") from None
        if not deleted:
            raise HTTPException(status_code=404, detail="Case not found")
        return {"deleted": True, "case_id": case_id}

    return application


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else "<unmatched>"


def analyze_message(
    text: str,
    user_notes: Optional[str] = None,
    store_case: Optional[bool] = None,
) -> AnalysisResult:
    """Compatibility wrapper for non-HTTP callers."""

    settings = Settings.from_env()
    resolved_store_case = settings.store_cases_by_default if store_case is None else store_case
    return create_analysis_service(settings=settings).analyze(
        AnalysisInput(text=text, user_notes=user_notes, store_case=resolved_store_case)
    )


app = create_app()
