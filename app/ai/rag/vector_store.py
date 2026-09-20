import os
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector

# langchain_postgres는 psycopg3 드라이버 사용 (postgresql+psycopg://)
_DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
    "postgresql://", "postgresql+psycopg://"
)

embeddings = OllamaEmbeddings(
    # 임베딩은 채팅 서버와 분리 가능 (미지정 시 OLLAMA_HOST/OLLAMA_MODEL 사용)
    model=os.getenv("OLLAMA_EMBED_MODEL", os.getenv("OLLAMA_MODEL")),
    base_url=os.getenv("OLLAMA_EMBED_HOST", os.getenv("OLLAMA_HOST")),
)

    
vector_store = PGVector(
    embeddings=embeddings,
    connection=_DATABASE_URL,
    collection_name="documents",
    use_jsonb=True,
)
