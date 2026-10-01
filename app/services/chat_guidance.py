"""Verified workspace instructions; no model or vector search required."""
import re

GUIDES = {
    "order": "상품은 다음 순서로 주문할 수 있어요.\n1. 메뉴에서 ‘상품 둘러보기’를 열어요.\n2. 상품명이나 카테고리로 검색한 뒤 ‘상품 상세 보기’를 눌러요.\n3. 재고 안에서 주문 수량을 정하고 ‘주문하기’를 눌러요. 로그인이 필요해요.\n4. 완료된 주문은 ‘내 주문’에서 확인할 수 있어요.\n현재 서비스는 주문 등록까지 지원하며, 결제 기능은 제공하지 않아요.",
    "product": "‘상품 둘러보기’에서 상품명과 카테고리로 검색할 수 있어요. ‘상품 상세 보기’를 누르면 가격과 재고를 확인할 수 있어요. 새 상품은 로그인 후 ‘상품 등록’에서 이름, 카테고리, 가격, 재고를 입력해 등록해요.",
    "account": "우측 상단의 계정 버튼에서 로그인할 수 있어요. 처음이라면 로그인 창의 ‘회원가입’을 선택해요. 로그인 후 계정 버튼을 누르면 내 정보를 확인하고 로그아웃할 수 있어요.",
    "document": "‘지식 문서’에서 ‘문서 추가’를 눌러 정책 내용을 등록해요. 기존 문서는 ‘수정하기’로 바꿀 수 있고, 저장된 문서는 AI의 정책 검색에 활용돼요.",
    "help": "상품 검색과 주문 방법, 내 주문 내역, 내 회원 정보, 등록된 배송·교환·환불 정책을 안내할 수 있어요. 예를 들어 ‘상품을 어떻게 주문해?’ 또는 ‘내 주문 내역 알려줘’라고 물어보면 돼요. 주문은 상품 화면에서 직접 확정해 주세요.",
}


def guidance_topic(message: str) -> str | None:
    text = re.sub(r"\s+", "", message.lower())
    # Policy questions must never be mistaken for purchase instructions.
    if any(word in text for word in ("환불", "교환", "배송", "반품", "취소")):
        return None
    how = any(word in text for word in ("어떻게", "어디서", "어디에서", "방법", "절차", "하려면", "하는법", "도와", "하고싶", "할래", "해줘", "해주", "할수"))
    if any(word in text for word in ("주문", "구매", "결제")) and how:
        if not any(word in text for word in ("내역", "조회", "주문한", "주문했")):
            return "order"
    if "상품" in text and how and any(word in text for word in ("등록", "검색", "찾", "보", "추가")):
        return "product"
    if how and any(word in text for word in ("로그인", "로그아웃", "회원가입")):
        return "account"
    if "문서" in text and how:
        return "document"
    if text in ("안녕", "안녕하세요", "도움말", "뭘할수있어", "무엇을할수있어", "뭐할수있어?"):
        return "help"
    return None


def service_guidance(message: str) -> str | None:
    topic = guidance_topic(message)
    return GUIDES.get(topic) if topic else None


def policy_fallback() -> str:
    return "등록된 문서에서 질문에 맞는 근거를 확인하지 못했어요. 어떤 상품이나 정책에 관한 질문인지 조금 더 구체적으로 알려주세요. 상품 주문 방법과 내 주문 내역도 안내할 수 있어요."
