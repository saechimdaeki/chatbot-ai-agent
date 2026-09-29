from __future__ import annotations

import os
import uuid

import numpy as np
import redis
from redis.commands.search.field import VectorField, TextField, TagField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

# TTL: 24시간 설정. 캐시 히트 시마다 갱신
CACHE_TTL = int(os.getenv("SEMANTIC_CACHE_TTL", 86400))

# 이후 변경될 데이터의 캐시 반환 방지를 위해 RAG(0.4)보다 임계치 훨씬 높게 설정
CACHE_THRESHOLD = 0.9

# 형식: semantic_cache:{member_id}:{uuid}
CACHE_PREFIX = "semantic_cache:"

INDEX_NAME = "idx:semantic_cache"


class SemanticCache:

    def __init__(self):
        self._available = False
        if os.getenv("USE_SEMANTIC_CACHE", "true").lower() == "false":
            print("[SemanticCache] 비활성화 (USE_SEMANTIC_CACHE=false)")
            return
        try:
            self.r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True,
            )
            self.r.ping()
            from app.ai.rag.vector_store import embeddings
            self.embeddings = embeddings
            # 모델마다 차원이 달라 실제 임베딩 길이로 결정
            self.vector_dim = len(embeddings.embed_query("dim"))
            self._ensure_index()
            self._available = True
            print("[SemanticCache] Redis 연결 성공")
        except Exception as e:
            # Redis 미실행 시에도 서버가 정상 동작하도록
            print(f"[SemanticCache] Redis 연결 실패 → 캐시 없이 동작: {e}")


    def _ensure_index(self):
        try:
            self.r.ft(INDEX_NAME).create_index(
                fields=[
                    TextField("question"),
                    TextField("response"),
                    TagField("member_id"),
                    VectorField(
                        "question_embedding",
                        "FLAT",
                        {"TYPE": "FLOAT32", "DIM": self.vector_dim, "DISTANCE_METRIC": "COSINE"},
                    ),
                ],
                definition=IndexDefinition(prefix=[CACHE_PREFIX], index_type=IndexType.HASH),
            )
            print(f"[SemanticCache] 인덱스 생성 완료: {INDEX_NAME}")
        except Exception:
            pass


    def store(self, question: str, response: str, member_id: int) -> None:
        if not self._available:
            return
        try:
            key = f"{CACHE_PREFIX}{member_id}:{uuid.uuid4()}"
            embedding = self._embed(question)

            self.r.hset(
                key,
                mapping={
                    "question": question.encode("utf-8"),
                    "response": response.encode("utf-8"),
                    "member_id": str(member_id),  
                    "question_embedding": embedding,
                },
            )
            self.r.expire(key, CACHE_TTL)
            print(f"[SemanticCache] 저장 완료 (member_id={member_id}, TTL: {CACHE_TTL}초): {question[:40]}...")

        except Exception as e:
            print(f"[SemanticCache] 저장 오류: {e}")

    def _embed(self, text: str) -> bytes:
        vector = self.embeddings.embed_query(text)
        return np.array(vector, dtype=np.float32).tobytes()

    def search(self, question: str, member_id: int) -> str | None:
        if not self._available:
            return None
        try:
            query_embedding = self._embed(question)

            q = (
                Query(f"(@member_id:{{{member_id}}})=>[KNN 1 @question_embedding $vec AS score]")
                .sort_by("score")
                .return_fields("response", "score")
                .dialect(2)
            )
            results = self.r.ft(INDEX_NAME).search(
                q, query_params={"vec": query_embedding}
            )

            if not results.docs:
                print(f"[SemanticCache] 검색 결과 없음 (member_id={member_id})")
                return None

            doc = results.docs[0]
            # Redis COSINE distance는 거리를 의미하므로, distance와 유사성은 반대의미
            distance = float(doc.score)
            similarity = 1 - distance

            print(f"[SemanticCache] 유사도: {similarity:.4f} (member_id={member_id})")

            if similarity < CACHE_THRESHOLD:
                print("[SemanticCache] 미스")
                return None
            
            self.r.expire(doc.id, CACHE_TTL)
            response = doc.response
            if isinstance(response, bytes):
                response = response.decode("utf-8")
            return response

        except Exception as e:
            print(f"[SemanticCache] 검색 오류: {e}")
            return None


    def flush_by_member(self, member_id: int) -> int:
    
        if not self._available:
            return 0
        try:
            keys = self.r.keys(f"{CACHE_PREFIX}{member_id}:*")
            if keys:
                self.r.delete(*keys)
            return len(keys)
        except Exception as e:
            return 0

    def flush(self) -> int:
        if not self._available:
            return 0
        try:
            keys = self.r.keys(f"{CACHE_PREFIX}*")
            if keys:
                self.r.delete(*keys)
            print(f"[SemanticCache] 전체 캐시 flush 완료: {len(keys)}개 삭제")
            return len(keys)
        except Exception as e:
            print(f"[SemanticCache] flush 오류: {e}")
            return 0

semantic_cache = SemanticCache()
