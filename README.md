# 모아

쇼핑몰의 주문·회원 정보와 정책 문서를 연결한 AI 상담 서비스입니다.

“내 주문 내역 알려줘”는 DB를 조회하고, “환불 정책이 궁금해”는 등록된 문서를 검색합니다. 상품 주문 방법처럼 정해진 사용법은 별도로 안내합니다. 질문의 성격에 따라 데이터와 답변 방식을 나누는 데 초점을 맞췄습니다.

회원·상품·주문 API에서 시작해 정책 검색, 대화 기록, Langfuse 추적을 붙였고, 기능을 직접 사용해 볼 수 있도록 웹 화면을 추가했습니다.

![모아 대시보드](docs/screenshots/dashboard.jpg)

## 주요 기능

- **회원** — 이메일 회원가입, JWT 로그인, 내 정보 조회
- **상품·주문** — 상품 등록과 검색, 상세 조회, 수량 선택, 주문 내역 확인
- **AI 상담** — 서비스 사용법 안내, 본인 주문·회원 정보 조회, 정책 문서 기반 답변
- **문서 관리** — 정책 문장 등록·조회·수정, 임베딩 저장
- **대화 기록** — 계정별 기록 저장과 이전 대화 조회
- **모니터링** — Langfuse에서 질문, 답변, 모델 호출과 소요 시간 확인

주문 등록까지 구현되어 있으며 결제와 주문 취소는 지원하지 않습니다.

## 화면

### AI 상담

질문을 입력하거나 추천 질문을 선택해 대화를 시작합니다. 로그인하거나 새로고침하면 빈 화면으로 시작하고, 과거 대화는 **이전 기록**에서 따로 확인합니다.

![AI 상담](docs/screenshots/chat.jpg)

### 상품과 주문

상품명·카테고리로 검색하고, 상세 화면에서 수량과 총액을 확인한 뒤 주문합니다. 상품 등록과 주문에는 로그인이 필요합니다. 주문이 완료되면 재고를 차감하고 **내 주문**에서 결과를 확인할 수 있습니다.

![상품 목록](docs/screenshots/products.jpg)

<details>
<summary>주문 상세 화면</summary>

![상품 상세 및 주문](docs/screenshots/product-detail.jpg)

</details>

### 정책 문서

배송·교환·환불 정책을 등록하거나 수정합니다. 저장한 문장은 임베딩되어 정책 질문의 검색 대상이 됩니다.

![정책 문서 관리](docs/screenshots/documents.jpg)

<details>
<summary>회원가입 · 로그인 · 계정 화면</summary>

이메일과 비밀번호로 로그인합니다. 가입 시 이름을 함께 입력하며, 로그인 후 계정 메뉴에서 회원 정보와 가입일을 확인할 수 있습니다. 토큰은 탭의 `sessionStorage`에 저장합니다.

| 로그인 | 회원가입 |
|---|---|
| ![로그인](docs/screenshots/login.jpg) | ![회원가입](docs/screenshots/signup.jpg) |

아래는 로그인 전 주문·회원 정보 화면입니다. 로그인 후에는 본인 데이터가 표시됩니다.

| 내 주문 | 내 정보 |
|---|---|
| ![주문 로그인 안내](docs/screenshots/orders-guest.jpg) | ![회원 정보 로그인 안내](docs/screenshots/profile-guest.jpg) |

</details>

<details>
<summary>프로젝트 소개 화면</summary>

![프로젝트 소개](docs/screenshots/about.jpg)

</details>

화면은 토스 디자인 가이드의 색상과 여백을 참고했습니다. HTML·CSS·JavaScript로 작성했으며, FastAPI가 `/workspace/`에서 정적 파일을 제공합니다. 별도 프론트엔드 빌드는 필요하지 않습니다.

## 질문을 처리하는 방식

채팅 요청은 `POST /chats`로 들어옵니다. 먼저 서비스 사용법에 해당하는지 확인하고, 나머지는 Ollama의 도구 호출로 분류합니다.

| 질문 | 처리 방식 |
|---|---|
| “상품을 주문하려면 어떻게 해야 해?” | 화면에 맞춰 작성한 주문 절차 안내 |
| “내 주문 내역 알려줘” | 로그인한 회원의 주문을 DB에서 조회 |
| “내 회원 정보 알려줘” | 현재 회원 정보를 DB에서 조회 |
| “환불 정책이 궁금해” | 문서 검색 후 검색 결과를 바탕으로 답변 생성 |

주문·회원 정보는 조회 결과를 그대로 형식화합니다. 모델이 이름이나 수량을 바꾸지 않도록 하기 위한 선택입니다. 정책 답변은 pgvector 검색 결과 중 유사도 `0.4` 이상인 문장을 최대 3개 사용합니다. 관련 문서가 없으면 필요한 정보를 다시 묻습니다.

정책 질문에는 계정의 최근 5개 질의응답도 전달합니다. 이전 대화는 질문의 맥락을 이해하는 용도로 사용하고, 답변 근거는 현재 검색한 문서를 우선하도록 구성했습니다. 화면에서 대화를 비우는 것과 서버의 대화 문맥을 초기화하는 것은 별개입니다.

### 주문 안내가 실패했던 문제

초기에는 주문·회원 조회로 분류되지 않은 질문을 전부 정책 검색으로 넘겼습니다. 그 결과 “상품을 주문하려면 어떻게 해야 하지”에도 배송·환불 문서가 검색되어 `응답불가합니다`라는 답변이 나왔습니다.

서비스 사용법을 별도 경로로 분리하고 모델 분류에도 `get_service_help`를 추가했습니다. 정해진 사용법은 모델 호출 전에 안내하며, 분류되지 않은 질문에는 지원하는 기능을 설명합니다. 실패 응답이 반복되는 것을 막기 위해 대화 API의 시맨틱 캐시 조회·저장도 중단했습니다.

## 기술 스택

| 구분 | 사용 기술 |
|---|---|
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Frontend | HTML, CSS, JavaScript |
| Database | PostgreSQL, pgvector |
| 인증 | JWT, bcrypt |
| LLM | Ollama, LangChain |
| 모델 구성 | 원격 `ornith:35b`, 로컬 폴백 `llama3.2:3b`, 임베딩 `bge-m3` |
| 모니터링 | Langfuse |
| 로컬 인프라 | Docker Compose, Redis Stack, ClickHouse, MinIO |

모델 주소와 이름은 환경변수로 설정합니다. 채팅 서버와 임베딩 서버를 분리할 수 있으며, 메인 모델 호출 실패 시 폴백 모델을 사용하도록 구성했습니다.

## Langfuse

질문 하나가 어떤 호출을 거쳐 답변이 되었는지 Langfuse에서 확인할 수 있습니다. 내부 답변 함수에 `@observe(name="chat")`를 적용하고, 모델 호출은 OpenAI 호환 클라이언트와 LangChain 콜백으로 기록합니다.

![Langfuse 관찰 기록](docs/screenshots/langfuse-observations.png)

위 기록에는 같은 주문 방법 질문에 대한 실패 응답과 수정 후 응답이 함께 남아 있습니다. 이전에는 모델 호출과 정책 답변 생성까지 진행됐지만, 수정 후에는 주문 절차를 바로 반환합니다. 이 경로에서는 하위 모델 호출이 생기지 않습니다.

**확인 순서**

1. [localhost:3000](http://localhost:3000)에서 프로젝트를 선택합니다.
2. 프로젝트 API 키를 발급해 `.env`에 넣고 FastAPI를 재시작합니다.
3. 채팅으로 질문을 보낸 뒤 **Tracing → Traces / Observations**를 엽니다.
4. `chat`의 Input·Output과 하위 모델 호출을 확인합니다. Latency, Model, Tokens로 호출 시간과 사용 모델, 토큰 수를 비교할 수 있습니다.

`Total Cost`는 모델 가격 설정에 따른 값입니다. 로컬 Ollama의 `$0.00` 표시는 GPU·서버 운영비를 포함하지 않습니다. 질문과 답변 본문도 기록되므로 실제 서비스에 적용할 때는 기록 범위를 정해야 합니다.

## 실행 방법

Python, Docker Compose, Ollama가 필요합니다. 프론트엔드 실행에는 Node.js가 필요하지 않습니다.

### 1. 의존성과 인프라

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d

ollama pull bge-m3
ollama pull llama3.2:3b
```

Compose는 PostgreSQL·Redis와 Langfuse 관련 서비스를 실행합니다. Python API는 별도로 실행합니다. PostgreSQL 최초 볼륨 생성 시 `init.sql`로 Langfuse DB도 준비합니다.

### 2. 환경변수

프로젝트 루트에 `.env`를 작성합니다. `OLLAMA_HOST`는 메인 모델 서버 주소로, Langfuse 키는 프로젝트에서 발급받은 값으로 바꿉니다.

```dotenv
DATABASE_URL=postgresql://myuser:mysecretpassword@localhost:5432/ai_agent_db
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=3000

OLLAMA_HOST=http://your-ollama-server:11434
OLLAMA_MODEL=ornith:35b
OLLAMA_FALLBACK_HOST=http://localhost:11434
OLLAMA_FALLBACK_MODEL=llama3.2:3b
OLLAMA_EMBED_HOST=http://localhost:11434
OLLAMA_EMBED_MODEL=bge-m3

USE_SEMANTIC_CACHE=false
REDIS_HOST=localhost
REDIS_PORT=6379

LANGFUSE_PUBLIC_KEY=pk-lf-your-project-key
LANGFUSE_SECRET_KEY=sk-lf-your-project-key
LANGFUSE_BASE_URL=http://localhost:3000
```

메인 모델은 도구 호출을 지원해야 합니다. 임베딩 모델을 변경해 벡터 차원이 바뀌면 기존 문서도 다시 임베딩해야 합니다. `.env`는 Git에서 제외되며 Compose의 기본 비밀번호는 로컬 개발용입니다.

### 3. 서버 실행

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- [서비스 화면](http://localhost:8000/workspace/)
- [Swagger API 문서](http://localhost:8000/docs)
- [Langfuse](http://localhost:3000)
- [RedisInsight](http://localhost:8001)

서버 시작 시 DB와 벡터 저장소를 초기화하므로 PostgreSQL이 먼저 실행되어 있어야 합니다. 기존 DB 볼륨을 사용한다면 Langfuse용 DB가 생성되어 있는지도 확인합니다.

<details>
<summary>DB 없이 화면만 확인하기</summary>

```bash
python3 frontend/preview.py
```

[localhost:8080/workspace/](http://localhost:8080/workspace/)에서 디자인만 확인할 수 있습니다. 이 서버는 API 요청에 503 안내를 반환하므로 로그인과 주문은 동작하지 않습니다. 실제 기능은 **8000번 FastAPI 서버**에서 사용합니다.

</details>

## API

인증이 필요한 요청에는 `Authorization: Bearer <access_token>`을 전달합니다. 요청·응답 스키마는 `/docs`에서 확인할 수 있습니다.

| 메서드 | 경로 | 기능 | 인증 |
|---|---|---|---|
| POST | `/members/signup` | 회원가입: email, password, 선택 name·age | 없음 |
| POST | `/members/login` | JWT 발급 | 없음 |
| GET | `/members/me` | 본인 정보 | 필요 |
| GET | `/products` | 이름·카테고리 부분 검색 | 없음 |
| GET | `/products/{product_id}` | 상품 상세, 없으면 404 | 없음 |
| POST | `/products` | 상품 등록: name, category, price, stock | 필요 |
| POST | `/orders` | 상품 ID·수량으로 주문 등록 | 필요 |
| GET | `/orders/me` | 본인 주문 목록 | 필요 |
| POST | `/chats` | 메시지 처리 후 질의응답 저장 | 필요 |
| GET | `/chats/me` | 본인의 최근 100개 질의응답, 오래된 순서 | 필요 |
| POST | `/chats/tunning` | 실험용 sLLM 의도 분류 | 필요 |
| GET | `/documents` | 임베딩 문서 목록 | 없음 |
| POST | `/documents` | `texts` 문자열 배열 저장 | 없음 |
| PUT | `/documents/{chunk_id}` | 기존 문서를 새 내용으로 교체 | 없음 |

주문 수량은 양의 정수, 가격과 재고는 0 이상으로 검증합니다. 동시 주문에서는 상품 행을 잠근 뒤 재고를 확인하고 차감합니다. 문서는 `texts`의 각 문자열 단위로 저장하며, 수정 시 기존 임베딩을 삭제한 뒤 새 UUID로 저장합니다.

## 추가로 다룬 내용

**검색과 캐시**

BM25 검색과 RRF 결합 함수, Redis 벡터 검색 기반 시맨틱 캐시를 작성했습니다. 현재 정책 검색에는 dense 검색만 연결되어 있고, 대화 API에서는 캐시를 사용하지 않습니다. 관련 코드는 `app/ai/rag/`에 있습니다.

**sLLM과 LoRA**

`app/ai/sllm_pinetunning/`에 데이터 구성, LoRA 학습, 모델 업로드·테스트, Ollama `Modelfile`을 모았습니다. `/chats/tunning`은 로컬 `llama3.2:3b`로 주문·회원·정책의 세 가지 의도를 분류하는 실험용 API입니다. 기본 채팅 API와는 별도 경로입니다.

## 코드 위치

| 경로 | 내용 |
|---|---|
| `app/routers/` | 회원·상품·주문·대화·문서 API |
| `app/models/`, `app/schemas/` | DB 모델과 요청·응답 스키마 |
| `app/services/` | 인증, 서비스 사용법 안내 |
| `app/ai/classification/` | 도구 정의와 질문 분류 |
| `app/ai/rag/` | 문서 검색, 대화 문맥, 답변 생성, 캐시 |
| `app/ai/sllm_pinetunning/` | sLLM 분류와 LoRA 실험 |
| `frontend/` | 화면과 API 호출 |
| `tests/` | Python·JavaScript 회귀 테스트 |

## 테스트

```bash
.venv/bin/python -m unittest discover -s tests -v
node --test tests/chat-ui.test.cjs
node --check frontend/app.js
```

입력 검증, 사용자별 대화 조회, 주문 재고 처리, 서비스 안내 분기, 대화 화면 초기 상태를 테스트합니다. DB·모델은 테스트 대역을 사용하므로 실제 동시 주문과 모델 답변 품질은 별도 검증이 필요합니다.

현재 보완할 부분은 대화 세션별 문맥 분리, 문서 관리 권한, 문서 교체 중 실패 복구입니다. 특히 문서 API는 아직 인증 없이 접근할 수 있습니다.
