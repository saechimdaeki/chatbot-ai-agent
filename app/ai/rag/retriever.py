from sqlalchemy import text
from langchain_community.retrievers import BM25Retriever

from app.database import engine
from .vector_store import vector_store

# 1에 가까울수록 엄격한 필터링
SIMILARITY_THRESHOLD = 0.4

def search_policy(query: str) -> str | None:
    results = vector_store.similarity_search_with_relevance_scores(query, k=3)
    for doc, score in results:
        print(f"{score:.4f} | {doc.page_content}")
    relevant = [doc.page_content for doc, score in results if score >= SIMILARITY_THRESHOLD]
    print(relevant)
    if not relevant:
        return None
    return "\n".join(relevant)


def _get_bm25_results(query: str) -> list:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT document FROM langchain_pg_embedding"))
        all_texts = [row[0] for row in rows]
    if not all_texts:
        return []
    retriever = BM25Retriever.from_texts(all_texts)
    retriever.k = 3
    return retriever.invoke(query)


def _reciprocal_rank_fusion(results_lists: list, k: int = 60) -> list:
    # k=60은 RRF 논문에서 권장하는 기본값
    scores: dict = {}
    for results in results_lists:
        for rank, doc in enumerate(results):
            key = doc.page_content
            if key not in scores:
                scores[key] = {"score": 0.0, "doc": doc}
            scores[key]["score"] += 1 / (rank + k)
    return sorted(scores.values(), key=lambda x: x["score"], reverse=True)


