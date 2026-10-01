from src.config import settings
from src.modules.auth.service.password_service import deliver_mail
from src.modules.mail import dispatch_mail

FEEDBACK_SUBJECT_PREFIX = "BScout: сообщение с формы контактов"


async def submit_feedback(name: str, email: str, subject: str, message: str) -> None:
    recipient = settings.support_email
    full_subject = f"{FEEDBACK_SUBJECT_PREFIX} — {subject}"
    text = f"Имя: {name}\nEmail для ответа: {email}\n\n{message}"
    await dispatch_mail(deliver_mail, recipient, full_subject, text, None)
