"""HTTP application boundary for FraudLens Bharat."""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from fraudlens.analysis_service import (
    AnalysisInput,
    CaseStore,
    DatabaseCaseStore,
    build_complaint_draft,
    create_analysis_service,
    resolve_predictor,
)
from fraudlens.prediction import Predictor, PredictorRegistry
from fraudlens.schemas import AnalysisResult, AnalyzeRequest
from fraudlens.settings import Settings


def create_app(
    settings: Optional[Settings] = None,
    predictor: Optional[Predictor] = None,
    store: Optional[CaseStore] = None,
    predictor_registry: Optional[PredictorRegistry] = None,
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

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.settings = resolved_settings
        application.state.case_store = resolved_store
        initializer = getattr(resolved_store, "initialize", None)
        if initializer is not None:
            try:
                initializer()
            except Exception:
                raise RuntimeError("Case storage initialization failed") from None
        application.state.analysis_service = create_analysis_service(
            settings=resolved_settings,
            predictor=resolved_predictor,
            store=resolved_store,
        )
        yield

    application = FastAPI(
        title="FraudLens Bharat Phase 1 API",
        description="Baseline cyber-fraud triage API for Hinglish/Hindi/English scam messages.",
        version="0.1.0",
        lifespan=lifespan,
    )
    if resolved_settings.allowed_hosts:
        application.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=list(resolved_settings.allowed_hosts),
        )

    @application.middleware("http")
    async def add_api_security_headers(request: Request, call_next):
        response = await call_next(request)
        if response.headers.get("content-type", "").startswith("application/json"):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "fraudlens-bharat-phase-1"}

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
    def delete_case(case_id: str, request: Request) -> dict:
        try:
            deleted = request.app.state.case_store.delete(case_id)
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error") from None
        if not deleted:
            raise HTTPException(status_code=404, detail="Case not found")
        return {"deleted": True, "case_id": case_id}

    return application


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
