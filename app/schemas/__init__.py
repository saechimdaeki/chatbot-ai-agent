from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class MemberCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    age: Optional[int] = None


class MemberResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    age: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    price: float = Field(ge=0, allow_inf_nan=False)
    stock: int = Field(ge=0)


class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    stock: int
    member_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderResponse(BaseModel):
    id: int
    member_id: int
    product_id: int
    quantity: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    id: int
    member_id: int
    request: str
    response: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    texts: list[str]

class DocumentResponse(BaseModel):
    added: int

class DocumentChunk(BaseModel):
    id: str       # langchain_pg_embedding의 UUID
    content: str

class DocumentChunkUpdate(BaseModel):
    text: str     # 수정할 새 텍스트 (기존 청크를 삭제하고 재임베딩 후 저장)
