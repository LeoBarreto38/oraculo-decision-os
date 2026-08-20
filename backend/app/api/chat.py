from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.api import ChatConfirmRequest, ChatRequest
from app.services.chat import answer_chat, confirm_chat_actions


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    return answer_chat(db, payload.message, payload.use_ai)


@router.post("/{message_id}/confirm")
def confirm_actions(message_id: int, payload: ChatConfirmRequest, db: Session = Depends(get_db)):
    try:
        return confirm_chat_actions(db, message_id, payload.action_indexes)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
