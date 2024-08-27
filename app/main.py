from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import model
from .schemas.database import engine
from .router.user import user

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user, prefix="/user", tags=["User"])


@app.get("/callback")
def read_root():
    return {"Hello": "Welcome to dashie!"}


model.data.metadata.create_all(bind=engine)
