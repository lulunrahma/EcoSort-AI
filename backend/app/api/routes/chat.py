from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.pydantic_models import ChatRequest, ChatResponse
from backend.app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])

@router.post("", response_model=ChatResponse)
def chat_with_bot(req: ChatRequest, db: Session = Depends(get_db)):
    """Conversational AI Assistant endpoint for EcoSort AI."""
    history_dicts = [h.model_dump() for h in req.history] if req.history else []
    res = ChatService.generate_reply(db=db, user_message=req.message, history=history_dicts)
    return ChatResponse(
        reply=res["reply"],
        suggested_actions=res.get("suggested_actions"),
        stats_context=res.get("stats_context")
    )

