from fastapi import APIRouter, Depends, status
from langfuse import observe
from sqlalchemy.orm import Session

from app import models, schemas
from app.services.chat_guidance import service_guidance, GUIDES, policy_fallback
from app.ai.classification.llm_calling import classify_message
from app.ai.rag.llm_calling_langchain import generate_response_langchain_memory
from app.ai.rag.memory import load_chat_history
from app.ai.rag.retriever import search_policy
from app.dependencies import get_db, get_current_member
from app.routers.member import my_page
from app.routers.order import my_orders

router = APIRouter(prefix="/chats", tags=["chat"])


@router.get("/me", response_model=list[schemas.ChatResponse])
def my_chats(
    db: Session = Depends(get_db),
    current_member: models.Member = Depends(get_current_member),
):
    """Return this member's latest 100 exchanges in chronological order."""
    records = (
        db.query(models.Chat)
        .filter(models.Chat.member_id == current_member.id)
        .order_by(models.Chat.created_at.desc(), models.Chat.id.desc())
        .limit(100)
        .all()
    )
    return list(reversed(records))


@router.post("", response_model=schemas.ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
    body: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_member: models.Member = Depends(get_current_member),
):
    # 엔드포인트에 바로 @observe를 걸면 db 세션/회원 ORM(비밀번호 해시 포함)까지 캡처됨
    # → 질문(str) → 응답(str)만 받는 내부 함수로 감싸 자동 캡처가 깔끔하게 남도록 함
    @observe(name="chat")
    def answer(message: str) -> str:
        # Instructions take precedence over stale cached failures and model routing.
        guidance = service_guidance(message)
        if guidance:
            return guidance

        action = classify_message(message)
        if action == "get_service_help":
            return GUIDES["help"] + "\n\n" + GUIDES["order"]
        if action == "get_my_orders":
            orders = my_orders(db=db, current_member=current_member)
            return _format_orders(orders)
        if action == "get_my_profile":
            # Account facts must not be rewritten or invented by an LLM.
            return _format_profile(my_page(current_member=current_member))
        if action != "get_policy":
            return GUIDES["help"]

        context = search_policy(message)
        if not context:
            return policy_fallback()
        history = load_chat_history(current_member.id, db)
        response_text = generate_response_langchain_memory(message, context, history)
        if not response_text or any(marker in response_text for marker in ("응답불가", "답변이 어려운 질문")):
            return policy_fallback()
        # Context-dependent answers are not reused solely by question similarity.

        return response_text

    response_text = answer(body.message)

    chat_record = models.Chat(
        member_id=current_member.id,
        request=body.message,
        response=response_text,
    )

    db.add(chat_record)
    db.commit()
    db.refresh(chat_record)
    return chat_record


def _format_orders(orders: list) -> str:
    if not orders:
        return "주문 내역이 없습니다."
    lines = [
        f"- 주문번호: {o.id} / 상품명: {o.product.name} / 수량: {o.quantity} / 주문일: {o.created_at.strftime('%Y-%m-%d')}"
        for o in orders
    ]
    return "\n".join(lines)


def _format_profile(member: list) -> str:
    if not member:
        return "회원정보가 없습니다."
    return f"- 회원번호: {member.id} / email: {member.email} / 회원명: {member.name} / age: {member.age} "


from app.ai.sllm_pinetunning.sllm_classification import sllm_classifier
@router.post("/tunning")
def create_chat_tunning(
    body: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_member: models.Member = Depends(get_current_member),
):
    action = sllm_classifier(body.message)
    print(action)
    return {"action": action}
