from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .schemas import model
from .schemas.database import engine
from .router.user import user
from .router.play import play
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Secret = os.getenv("SECRET")
app.add_middleware(SessionMiddleware, secret_key=Secret)
app.include_router(user, prefix="/user", tags=["User"])
app.include_router(play, prefix="/play", tags=["Play"])


@app.get("/dashboard")
def read_root(request: Request):
    token = request.session.get("access_token")
    if token is None:
        return RedirectResponse(url="/user/login")

    return {"message": "Welcome to the dashboard"}


model.data.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {"message": "Welcome to the Spotify API"}

