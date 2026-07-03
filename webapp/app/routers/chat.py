import os

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import agent, schemas
from ..database import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse)
def chat(data: schemas.ChatRequest, db: Session = Depends(get_db)):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY غير مضبوط — أضفه في ملف .env لتفعيل المساعد الذكي",
        )
    try:
        reply, tools_used = agent.chat(db, data.session_id, data.message)
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=503, detail="مفتاح API غير صالح")
    except anthropic.APIStatusError as exc:
        raise HTTPException(status_code=502, detail=f"خطأ من واجهة الذكاء الاصطناعي: {exc.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=502, detail="تعذر الاتصال بواجهة الذكاء الاصطناعي")
    return schemas.ChatResponse(reply=reply, tools_used=tools_used)


@router.delete("/{session_id}", status_code=204)
def reset(session_id: str):
    agent.reset_session(session_id)
