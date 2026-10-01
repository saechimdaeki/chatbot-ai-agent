from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.database import engine, Base
from app.routers import member, product, order, chat
from app.routers import document

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Agent API")

app.include_router(member.router)
app.include_router(product.router)
app.include_router(order.router)
app.include_router(chat.router)
app.include_router(document.router)

app.mount("/workspace", StaticFiles(directory=Path(__file__).resolve().parent.parent / "frontend", html=True), name="workspace")


@app.get("/", include_in_schema=False)
def workspace():
    return RedirectResponse("/workspace/")
