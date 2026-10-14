from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Smart Access AI Service", version="0.1.0", description="Inference interface; face verification is intentionally a placeholder.")

class VerificationRequest(BaseModel):
    subject_reference: str = Field(..., min_length=1, max_length=128)
    image_reference: str = Field(..., min_length=1, max_length=512)

class VerificationResponse(BaseModel):
    status: Literal["NOT_IMPLEMENTED"]
    verified: bool
    score: float | None = None
    model_version: str = "placeholder"
    detail: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "smart-access-ai"}

@app.post("/v1/face/verify", response_model=VerificationResponse)
def face_verify(payload: VerificationRequest):
    # Always fail closed until a validated model and enrolment workflow are implemented.
    return VerificationResponse(status="NOT_IMPLEMENTED", verified=False, score=None, model_version="placeholder", detail="No face-verification model is configured. Access must not be granted based on this endpoint.")
