import uuid

from fastapi import APIRouter, HTTPException, Request, Response, status

from src.modules.trial.schema.trial import (
    TrialSearchRequest,
    TrialSearchResponse,
    TrialStatusResponse,
)
from src.modules.trial.service.trial_service import TrialService

router = APIRouter(prefix="/api/trial", tags=["trial"])

TRIAL_COOKIE_NAME = "bscout_trial_id"
TRIAL_COOKIE_MAX_AGE = 60 * 60 * 24 * 30


def _get_or_create_client_id(request: Request, response: Response) -> str:
    client_id = request.cookies.get(TRIAL_COOKIE_NAME)
    if not client_id:
        client_id = str(uuid.uuid4())
        response.set_cookie(
            TRIAL_COOKIE_NAME,
            client_id,
            max_age=TRIAL_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            path="/",
        )
    return client_id


@router.get("/status", response_model=TrialStatusResponse)
async def get_trial_status(request: Request, response: Response):
    client_id = _get_or_create_client_id(request, response)
    used = await TrialService.is_used(client_id)
    return TrialStatusResponse(available=not used, client_id=client_id)


@router.post("/search", response_model=TrialSearchResponse)
async def run_trial_search(body: TrialSearchRequest, request: Request, response: Response):
    client_id = _get_or_create_client_id(request, response)
    used = await TrialService.is_used(client_id)
    if used:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trial search has already been used",
        )

    await TrialService.mark_used(client_id, query=body.query)
    return TrialSearchResponse(results=[], total=0, page=1, per_page=20, query=body.query)
