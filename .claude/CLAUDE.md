# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## Project: chatbot-ai-agent

FastAPI backend (Korean e-commerce chatbot): members/products/orders + LLM chat with intent classification, RAG, semantic cache.

### Commands
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
docker compose up -d            # pgvector/pg16 on 5432, runs init.sql (CREATE EXTENSION vector)
ollama pull bge-m3              # embedding model
uvicorn app.main:app --reload
```
No test suite exists.

### Layout
- `app/main.py` — app + router registration; tables via `Base.metadata.create_all` (no migrations)
- `app/routers/chat.py` — main flow: semantic cache → classify → route (orders/profile/policy) → cache + persist `Chat`
- `app/ai/classification/` — tool-call intent classification (openai SDK → Ollama `/v1`)
- `app/ai/rag/` — PGVector store, retriever (threshold 0.4), Redis semantic cache, chat memory, LangChain LLM calls
- `app/ai/sllm_pinetunning/pinetunning/` — offline LoRA pipeline for llama3.2:3b; own `requirements.txt`, GPU only, not part of the app venv

### Env (.env, gitignored)
`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_EMBED_HOST`, `OLLAMA_EMBED_MODEL`, `USE_SEMANTIC_CACHE`, `REDIS_HOST`/`REDIS_PORT` (default localhost:6379)

### Gotchas
- Three Ollama endpoints: `OLLAMA_HOST` (chat/classify), `OLLAMA_EMBED_HOST` (embeddings), and a hardcoded `localhost:11434` `llama3.2:3b` for the sLLM path (`/chats/tunning`, profile handler).
- Classify/generate exist twice: `classification/llm_calling.py` (openai SDK) and `rag/llm_calling_langchain.py`. `chat.py` uses `classify_message` + `generate_response_langchain`.
- Redis is not in `compose.yaml`; semantic cache fails open when Redis is down, so its absence is silent.
- `DATABASE_URL` is rewritten to `postgresql+psycopg://` for langchain-postgres. `routers/document.py` writes raw SQL to `langchain_pg_embedding`.
- `retriever.py` BM25/RRF hybrid helpers are not wired in (dead code).
