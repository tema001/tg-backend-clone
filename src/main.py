import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from uvicorn import run

from api.routers.users import router as users_router
from api.routers.files import router as router_router
from api.routers.auth import router as auth_router
from api.routers.ws import router as ws_router

from task_manager.domain.manager import TaskManager

from db import get_conversations, get_messages

from conversations.repository import ConversationRepository
from messages.repository import MessageRepository
from fastapi.middleware.cors import CORSMiddleware

tm = TaskManager(ConversationRepository(get_conversations()),
                 MessageRepository(get_messages())
                 )


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(tm.main_loop())
    yield
    tm.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(router_router)
app.include_router(auth_router)
app.include_router(ws_router)

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    run('main:app', host="0.0.0.0", port=8000, ws='websockets', ws_ping_interval=100.0)
