import os

from openai import OpenAI, APIConnectionError

from .classification_list import TOOLS

# Ollama의 OpenAI 호환 엔드포인트(/v1) 사용. api_key는 필수값이라 더미값
# 메인(GPU 노드)은 재시도 없이 바로 실패시켜 폴백으로 넘김
client = OpenAI(base_url=f"{os.getenv('OLLAMA_HOST')}/v1", api_key="ollama", max_retries=0)
MODEL = os.getenv("OLLAMA_MODEL")
FALLBACK_HOST = os.getenv("OLLAMA_FALLBACK_HOST")
FALLBACK_MODEL = os.getenv("OLLAMA_FALLBACK_MODEL")
fallback_client = OpenAI(base_url=f"{FALLBACK_HOST}/v1", api_key="ollama")


# ponytail: 매 요청마다 메인 먼저 시도(연결 타임아웃 5초). 노드가 오래 죽어있으면 그만큼 지연 → 필요 시 일정 시간 메인 건너뛰기 추가
def _chat(**kwargs):
    try:
        return client.chat.completions.create(model=MODEL, **kwargs)
    except APIConnectionError as e:
        print(f"[LLM] 메인 서버 연결 실패 → 폴백({FALLBACK_MODEL}) 사용: {e}")
        return fallback_client.chat.completions.create(model=FALLBACK_MODEL, **kwargs)


def classify_message(message: str) -> str:
    response = _chat(
        messages=[{"role": "user", "content": message}],
        tools=TOOLS,
        tool_choice="auto",
        temperature=0
    )
    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        return "답변이 어려운 질문입니다."
    return tool_calls[0].function.name

def generate_response(user_message: str, data: str) -> str:
    response = _chat(
        messages=[
            {
                "role": "system",
                "content": f"사용자의 질문에 대해 아래 참고 데이터를 바탕으로 사용자의 질문에 답변해. "
                           f"만약 참고데이터에 적절한 내용이 없으면 응답불가합니다 라고 답변해. \n\n[참고 데이터]\n{data}",
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()