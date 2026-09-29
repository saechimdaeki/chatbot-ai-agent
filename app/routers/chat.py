from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.ai.classification.llm_calling import classify_message, generate_response
from app.ai.rag.llm_calling_langchain import generate_response_langchain, generate_response_langchain_memory
from app.ai.rag.memory import load_chat_history
from app.ai.rag.retriever import search_policy
from app.ai.rag.semantic_cache import semantic_cache
from app.ai.sllm_pinetunning.sllm_model_request import generate_response_sllm
from app.dependencies import get_db, get_current_member
from app.routers.member import my_page
from app.routers.order import my_orders

router = APIRouter(prefix="/chats", tags=["chat"])


@router.post("", response_model=schemas.ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
    body: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_member: models.Member = Depends(get_current_member),
):
    cached_response = semantic_cache.search(body.message, current_member.id)
    if cached_response:
        response_text = cached_response

    else:
        action = classify_message(body.message)
        print(action)
        if action == "get_my_orders":
            orders = my_orders(db=db, current_member=current_member)
            print(orders)
            data = _format_orders(orders)
            print(data)
            response_text = generate_response(body.message, data)
        # 민감정보의 경우 sLLM을 통해 응답생성
        elif action == "get_my_profile":
            member = my_page(current_member=current_member)
            print(member)
            data = _format_profile(member)
            print(data)
            response_text = generate_response_sllm(body.message, data)
        else:
            context = search_policy(body.message)
            history = load_chat_history(current_member.id, db)
            response_text = generate_response_langchain_memory(body.message, context, history)

        # store: member_id 포함 (flush_by_member로 사용자별 선택 삭제 가능)
        semantic_cache.store(body.message, response_text, current_member.id)


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
