from pydantic import BaseModel, EmailStr, Field


class FeedbackRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)


class FeedbackResponse(BaseModel):
    detail: str
