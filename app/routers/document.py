from fastapi import APIRouter, Depends, HTTPException, status
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app import schemas
from app.ai.rag.semantic_cache import semantic_cache
from app.ai.rag.vector_store import vector_store
from app.dependencies import get_db

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
def add_documents(body: schemas.DocumentCreate, db: Session = Depends(get_db)):
    chunk_texts = [chunk for chunk in body.texts]

    vector_store.add_texts(chunk_texts)

    return {"added": len(body.texts)}

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)


@router.get("", response_model=list[schemas.DocumentChunk])
def list_documents(db: Session = Depends(get_db)):
    # Admin UI에서 청크 목록을 확인하고 수정 대상 UUID를 선택하기 위한 용도
    rows = db.execute(
        sql_text("SELECT id::text, document FROM langchain_pg_embedding ORDER BY id")
    ).fetchall()
    return [{"id": row[0], "content": row[1]} for row in rows]


@router.put("/{chunk_id}", response_model=schemas.DocumentChunk)
def upsert_document(chunk_id: str, body: schemas.DocumentChunkUpdate, db: Session = Depends(get_db)):
    existing = db.execute(
        sql_text("SELECT id FROM langchain_pg_embedding WHERE id = :id"),
        {"id": chunk_id}
    ).fetchone()

    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 청크를 찾을 수 없습니다.")

    vector_store.delete(ids=[chunk_id])

    # 새 UUID가 자동 부여됨 → 반환값으로 새 UUID를 확인 가능
    new_ids = vector_store.add_texts([body.text])

    # 청크 내용이 바뀌면 기존 캐시 응답이 outdated 될 수 있으므로 전체 삭제
    semantic_cache.flush()

    return {"id": new_ids[0], "content": body.text}
