"""
SATHEE / Mentor AI Hub & Admissions Router

Exposes cognitive AI, OMR evaluation, and admissions microservices inspired by
Ref_Docs/endpoints.md:
- POST /api/ai-hub/vision/ocr (Handwritten & Equation LaTeX OCR)
- POST /api/ai-hub/chat/stream (Server-Sent Events Streaming Socratic Doubt Solver)
- POST /api/ai-hub/qa/generate-similar-questions (Isomorphic Question Synthesizer)
- POST /api/ai-hub/rank/predict (Multi-Year Normalization Rank & Percentile Predictor)
- GET  /api/ai-hub/colleges/cutoffs (IIT/NIT/AIIMS Cutoff Explorer & Eligibility Check)
- POST /api/ai-hub/omr/evaluate (Physical OMR Sheet Scanner & Grader)

Author: Mentor AI Team
Version: 1.0.0
"""

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse

from models.marks_sathee_models import (
    GenerateSimilarQuestionsRequest,
    GenerateSimilarQuestionsResponse,
    OCRResponse,
    OMREvaluateResponse,
    RankPredictRequest,
    RankPredictResponse,
    StreamingDoubtRequest,
)
from services.ai_hub_admissions_service import AIHubAdmissionsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-hub", tags=["SATHEE AI Hub & Admissions"])

_ai_hub_service: Optional[AIHubAdmissionsService] = None


def get_ai_hub_service() -> AIHubAdmissionsService:
    global _ai_hub_service
    if _ai_hub_service is None:
        _ai_hub_service = AIHubAdmissionsService()
    return _ai_hub_service


@router.post(
    "/vision/ocr",
    response_model=OCRResponse,
    summary="Handwritten & Equation LaTeX OCR",
    description="Extracts mathematical formulas, LaTeX markup, and printed question text from an image.",
)
async def vision_ocr(
    image: Optional[UploadFile] = File(default=None),
    detectMath: bool = Form(default=True),
    language: str = Form(default="en"),
    textHint: Optional[str] = Form(default=None),
    service: AIHubAdmissionsService = Depends(get_ai_hub_service),
) -> OCRResponse:
    img_bytes = await image.read() if image is not None else None
    fname = image.filename if image is not None and image.filename else "upload.png"
    return service.extract_ocr(
        image_bytes=img_bytes,
        filename=fname,
        detect_math=detectMath,
        language=language,
        text_hint=textHint,
    )


@router.post(
    "/chat/stream",
    summary="Streaming Socratic AI Doubt Solver (SSE)",
    description="Streams deductive, step-by-step Socratic explanations using Server-Sent Events (text/event-stream).",
)
async def stream_socratic_doubt(
    request: StreamingDoubtRequest,
    service: AIHubAdmissionsService = Depends(get_ai_hub_service),
) -> StreamingResponse:
    return StreamingResponse(
        service.stream_socratic_doubt(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/qa/generate-similar-questions",
    response_model=GenerateSimilarQuestionsResponse,
    summary="Synthesize Isomorphic Practice Questions",
    description="Generates similar practice problems sharing identical concepts with altered numerical parameters.",
)
async def generate_similar_questions(
    request: GenerateSimilarQuestionsRequest,
    service: AIHubAdmissionsService = Depends(get_ai_hub_service),
) -> GenerateSimilarQuestionsResponse:
    return service.generate_similar_questions(request)


@router.post(
    "/rank/predict",
    response_model=RankPredictResponse,
    summary="AI All India Rank (AIR) & Category Percentile Predictor",
)
async def predict_rank(
    request: RankPredictRequest,
    service: AIHubAdmissionsService = Depends(get_ai_hub_service),
) -> RankPredictResponse:
    return service.predict_rank(request)


@router.get(
    "/colleges/cutoffs",
    summary="Query IIT/NIT/AIIMS College Cutoffs & Branch Eligibility",
)
async def get_college_cutoffs(
    collegeId: Optional[str] = Query(default=None, description="e.g. iit_bombay, nit_trichy, aiims_delhi"),
    exam: Optional[str] = Query(default=None, description="jee_advanced | jee_main | neet"),
    category: str = Query(default="General", description="General | OBC-NCL | SC | ST | EWS"),
    studentAir: Optional[int] = Query(default=None, ge=1, description="Optional predicted AIR to check branch eligibility"),
    service: AIHubAdmissionsService = Depends(get_ai_hub_service),
) -> Dict[str, Any]:
    return service.get_college_cutoffs(
        college_id=collegeId,
        exam=exam,
        category=category,
        student_air=studentAir,
    )


@router.post(
    "/omr/evaluate",
    response_model=OMREvaluateResponse,
    summary="Evaluate Physical OMR Answer Sheet",
    description="Grades a physical OMR bubble sheet against an exam template answer key.",
)
async def evaluate_physical_omr(
    omrImage: Optional[UploadFile] = File(default=None),
    templateId: str = Form(default="jee_advanced_paper1_2026"),
    rollNumber: str = Form(default="1029481"),
    scannedAnswersJson: Optional[str] = Form(
        default=None,
        description='Optional JSON object of detected bubbles, e.g. {"1": "A", "2": "C"}',
    ),
    service: AIHubAdmissionsService = Depends(get_ai_hub_service),
) -> OMREvaluateResponse:
    overrides = None
    if scannedAnswersJson:
        try:
            parsed = json.loads(scannedAnswersJson)
            if isinstance(parsed, dict):
                overrides = {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            pass
    return service.evaluate_omr(
        template_id=templateId,
        roll_number=rollNumber,
        scanned_overrides=overrides,
    )
