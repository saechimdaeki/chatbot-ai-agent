TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_service_help",
            "description": "서비스 사용법, 상품 주문·구매 방법, 상품 검색·등록 방법, 로그인·회원가입, 문서 관리 방법을 안내합니다. 주문하는 방법은 주문 내역 조회나 배송·환불 정책과 다릅니다.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_orders",
            "description": "로그인한 사용자 본인의 주문 내역을 조회합니다. '내 주문', '주문 내역', '내가 주문한 것' 등의 요청에 사용합니다.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_profile",
            "description": "로그인한 사용자 본인의 회원정보(이메일, 이름, 나이)를 조회합니다. '내 정보', '마이페이지', '내 계정', '내 이름' 등 질문의 대상이 '나'일 때만 사용합니다. 회사·대표·직원·판매자 등 다른 사람이나 회사에 대한 질문에는 사용하지 않습니다.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_policy",
            "description": "환불정책, 교환, 배송 등 사내정책 및 회사 정보(대표자, 연락처, 주소 등) 관련 질문에 답변합니다.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
