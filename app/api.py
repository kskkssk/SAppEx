from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from fastapi_redis_session import deleteSession, getSession, getSessionId, getSessionStorage, setSession, SessionStorage
import redis
import os
import uvicorn
from typing import Any
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

redis_instance = redis.Redis(host='redis', port=6379, db=0)

SECRET_KEY = os.getenv('SECRET_KEY')
REDIS_URL = os.getenv('REDIS_URL')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')


app.on_event('startup')

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.post("/setSession")
async def _setSession(
    request: Request, response: Response, sessionStorage: SessionStorage = Depends(getSessionStorage)
):
    sessionData = await request.json()
    setSession(response, sessionData, sessionStorage)


@app.get("/getSession")
async def _setSession(session: Any = Depends(getSession)):
    return session


@app.post("/deleteSession")
async def _deleteSession(
    sessionId: str = Depends(getSessionId), sessionStorage: SessionStorage = Depends(getSessionStorage)
):
    deleteSession(sessionId, sessionStorage)
    return None


def startup():
    init_db()


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8083)