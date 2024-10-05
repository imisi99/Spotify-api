from .database import begin
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session


def get_db():
    db = begin()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
