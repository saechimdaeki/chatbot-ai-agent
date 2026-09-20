import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from app.ai.classification.classification_list import TOOLS

llm_classify = ChatOllama(
    model=os.getenv("OLLAMA_MODEL"),
    base_url=os.getenv("OLLAMA_HOST"),
    temperature=0
)

llm_response = ChatOllama(
    model=os.getenv("OLLAMA_MODEL"),
    base_url=os.getenv("OLLAMA_HOST"),
    temperature=0.3
)

llm_with_tools = llm_classify.bind_tools(TOOLS)


def classify_message_langchain(message: str) -> str:
    response = llm_with_tools.invoke(message)
    tool_calls = response.tool_calls
    if not tool_calls:
        return "답변이 어려운 질문입니다."
    return tool_calls[0]["name"]


def generate_response_langchain(user_message: str, data: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "사용자의 질문에 대해 아래 참고 데이터를 바탕으로 사용자의 질문에 답변해. 만약 참고데이터에 적절한 내용이 없으면 응답불가합니다 라고 답변해. \n\n[참고 데이터]\n{data}"),
        ("user", "{user_message}"),
    ])
    chain = prompt | llm_response | StrOutputParser()
    return chain.invoke({"data": data, "user_message": user_message})


def generate_response_langchain_memory(user_message: str, data: str, history: list = None) -> str:
    print(f"generate_response memory back data {history}")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "사용자의 질문에 대해 아래 참고 데이터를 바탕으로 사용자의 질문에 답변해. "
            "이전 대화에서 답할 수 있는 내용이 있으면 그것을 우선으로 사용해."
            "만약 참고 데이터와 이전 대화 모두에서 관련 내용을 찾을 수 없는 경우에만 응답불가합니다 라고 답변해.\n\n"
            "[참고 데이터]\n{data}"
        ),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{user_message}"),
    ])
    chain = prompt | llm_response | StrOutputParser()
    return chain.invoke({
        "data": data or "",
        "user_message": user_message,
        "history": history or [],
    })


