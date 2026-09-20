import os
from openai import OpenAI
from .classification_list import TOOLS

# Ollama의 OpenAI 호환 엔드포인트(/v1) 사용. api_key는 필수값이라 더미값
client = OpenAI(base_url=f"{os.getenv('OLLAMA_HOST')}/v1", api_key="ollama")
MODEL = os.getenv("OLLAMA_MODEL")


def classify_message(message: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
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
    response = client.chat.completions.create(
        model=MODEL,
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