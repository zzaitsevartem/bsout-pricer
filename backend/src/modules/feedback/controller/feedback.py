from fastapi import APIRouter, status

from src.modules.feedback.schema.feedback import FeedbackRequest, FeedbackResponse
from src.modules.feedback.service.feedback import submit_feedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

FEEDBACK_ACCEPTED_DETAIL = "Сообщение отправлено. Мы ответим на указанную почту."


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_feedback(body: FeedbackRequest):
    await submit_feedback(
        name=body.name.strip(),
        email=str(body.email),
        subject=body.subject.strip(),
        message=body.message.strip(),
    )
    return FeedbackResponse(detail=FEEDBACK_ACCEPTED_DETAIL)
