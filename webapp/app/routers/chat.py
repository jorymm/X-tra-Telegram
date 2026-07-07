import os

from fastapi import APIRouter, Depends, HTTPException
from google.genai import errors as genai_errors
from sqlalchemy.orm import Session

from .. import agent, schemas
from ..database import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(data: schemas.ChatRequest, db: Session = Depends(get_db)):
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY غير مضبوط — احصل على مفتاح مجاني من aistudio.google.com وأضفه في ملف .env",
        )
    try:
        reply, tools_used = agent.chat(db, data.session_id, data.message)
    except genai_errors.APIError as exc:
        if exc.code == 429:
            raise HTTPException(
                status_code=429,
                detail="تجاوزت الحصة المجانية مؤقتاً — انتظر دقيقة ثم حاول مرة أخرى",
            )
        if exc.code in (401, 403):
            raise HTTPException(status_code=503, detail="مفتاح API غير صالح — تأكد من المفتاح في ملف .env")
        raise HTTPException(status_code=502, detail=f"خطأ من واجهة الذكاء الاصطناعي: {exc.message}")
    return schemas.ChatResponse(reply=reply, tools_used=tools_used)


@router.delete("/{session_id}", status_code=204)
def reset(session_id: str):
    agent.reset_session(session_id)
