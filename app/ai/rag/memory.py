from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy.orm import Session

from app.models import Chat

# 너무 크면 토큰 비용 증가, 너무 작으면 문맥 손실
MEMORY_WINDOW = 5


def load_chat_history(member_id: int, db: Session, limit: int = MEMORY_WINDOW) -> list:

    recent_chats = (
        db.query(Chat)
        .filter(Chat.member_id == member_id)
        .order_by(Chat.created_at.desc())
        .limit(limit)
        .all()
    )

    messages = []
    for chat in reversed(recent_chats):  # 앞의 5개 중 오래된 것부터
        messages.append(HumanMessage(content=chat.request))
        messages.append(AIMessage(content=chat.response))

    return messages
