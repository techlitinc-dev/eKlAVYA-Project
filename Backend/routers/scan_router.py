"""
Scan & Solve Router

Scan lifecycle endpoints, all registered under /api/v1: create scan,
upload pages (multipart), process with mock OCR, confirm OCR, execute an
intent, read OCR/result, and the result actions (save note, create mind
map, schedule revision).

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, File, Form, Header, Request, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.config import Settings, get_settings
from core.security import Principal, get_current_principal
from dependencies import IdempotencyManager, get_repository
from models.mindmaps import MindMap
from models.notes import Note
from models.planner import RevisionItem
from models.scans import (
    ExecuteIn,
    ExecutionOut,
    OcrConfirmIn,
    OcrOut,
    PageOut,
    ResultOut,
    ScanCreate,
    ScanOut,
)
from repositories.base import Repository
from services import scan_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Scans"])


@router.post(
    "/scans",
    response_model=ScanOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a scan",
)
def create_scan(
    payload: ScanCreate,
    request: Request,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("scan.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    scan = service.create_scan(repo, principal, payload)
    if idem_key:
        manager.store(
            "scan.create",
            idem_key,
            body,
            status.HTTP_201_CREATED,
            jsonable_encoder(scan),
        )
    return scan


@router.post(
    "/scans/{scan_id}/pages",
    response_model=PageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one scan page (multipart/form-data, field 'file')",
)
def upload_page(
    scan_id: str,
    request: Request,
    file: UploadFile = File(...),
    page_number: Optional[int] = Form(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    content = file.file.read()
    return service.upload_page(
        repo, principal, settings, scan_id, content, page_number
    )


@router.post(
    "/scans/{scan_id}/process",
    response_model=ScanOut,
    summary="Run mock OCR over all uploaded pages",
)
def process_scan(
    scan_id: str,
    request: Request,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    return service.process_scan(repo, principal, settings, scan_id)


@router.get(
    "/scans/{scan_id}",
    response_model=ScanOut,
    summary="Get a scan (owner or admin)",
)
def get_scan(
    scan_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    return service.get_scan(repo, principal, scan_id)


@router.get(
    "/scans/{scan_id}/ocr",
    response_model=OcrOut,
    summary="Get OCR output and uncertain regions",
)
def get_ocr(
    scan_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    return service.get_ocr(repo, principal, scan_id)


@router.put(
    "/scans/{scan_id}/ocr-confirmation",
    response_model=ScanOut,
    summary="Confirm or correct the OCR text",
)
def confirm_ocr(
    scan_id: str,
    payload: OcrConfirmIn,
    request: Request,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    return service.confirm_ocr(repo, principal, scan_id, payload.text)


@router.post(
    "/scans/{scan_id}/execute",
    response_model=ExecutionOut,
    summary="Execute the scan intent",
)
def execute_scan(
    scan_id: str,
    request: Request,
    payload: ExecuteIn = Body(default_factory=ExecuteIn),
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("scan.execute", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    scan, result = service.execute_scan(
        repo, principal, settings, scan_id, steps=payload.steps
    )
    execution = ExecutionOut(
        scan_id=scan.id,
        intent=result.intent,
        status=scan.status,
        payload=result.payload,
        grounding_status=result.grounding_status,
        verification_status=result.verification_status,
        citations=result.citations,
    )
    if idem_key:
        manager.store(
            "scan.execute",
            idem_key,
            body,
            status.HTTP_200_OK,
            jsonable_encoder(execution),
        )
    return execution


@router.get(
    "/scans/{scan_id}/result",
    response_model=ResultOut,
    summary="Get the latest execution result for a scan",
)
def get_result(
    scan_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    return service.get_result(repo, principal, scan_id)


@router.post(
    "/scans/{scan_id}/save-note",
    response_model=Note,
    status_code=status.HTTP_201_CREATED,
    summary="Save the scan result as a note (idempotent per scan)",
)
def save_note(
    scan_id: str,
    request: Request,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body: dict = {}
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("scan.save_note", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    note, created = service.save_note(repo, principal, scan_id)
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    if idem_key:
        manager.store(
            "scan.save_note", idem_key, body, status_code, jsonable_encoder(note)
        )
    if not created:
        return JSONResponse(status_code=status_code, content=jsonable_encoder(note))
    return note


@router.post(
    "/scans/{scan_id}/create-mindmap",
    response_model=MindMap,
    status_code=status.HTTP_201_CREATED,
    summary="Create a mind map from the scan (idempotent per scan)",
)
def create_mindmap(
    scan_id: str,
    request: Request,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body: dict = {}
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("scan.create_mindmap", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    mind_map, created = service.create_mindmap(repo, principal, scan_id)
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    if idem_key:
        manager.store(
            "scan.create_mindmap",
            idem_key,
            body,
            status_code,
            jsonable_encoder(mind_map),
        )
    if not created:
        return JSONResponse(status_code=status_code, content=jsonable_encoder(mind_map))
    return mind_map


@router.post(
    "/scans/{scan_id}/schedule-revision",
    response_model=RevisionItem,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a revision item from the scan (idempotent per scan)",
)
def schedule_revision(
    scan_id: str,
    request: Request,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body: dict = {}
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("scan.schedule_revision", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    item, created = service.schedule_revision(repo, principal, scan_id)
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    if idem_key:
        manager.store(
            "scan.schedule_revision",
            idem_key,
            body,
            status_code,
            jsonable_encoder(item),
        )
    if not created:
        return JSONResponse(status_code=status_code, content=jsonable_encoder(item))
    return item
