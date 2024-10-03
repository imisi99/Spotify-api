import os
import jwt
from .database import begin
from jose import JWTError, jwt
from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime
from starlette import status


def get_db():
    db = begin()
    try:
        yield db
    finally:
        db.close()


secret = os.getenv('SECRET')
Algorithm = os.getenv('ALGORITHM')


def authentication(user_id: int, username: str, limit):
    encode = {'sub': username, 'id': user_id}
    exp = datetime.utcnow() + limit
    encode.update({'exp': exp})
    return jwt.encode(encode, )


bearer = OAuth2PasswordBearer(tokenUrl='user/login')


async def get_user(token: Annotated[str, Depends(bearer)]):
    try:
        payload = jwt.decode(token, secret, algorithms=[Algorithm])
        user_id = payload.get('id')
        username = payload.get('sub')

        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="An error occurred while logging-in please try again")
        return {
            'user_id': user_id,
            'username': username
        }
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An error occurred as {e}")


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Session, Depends(get_user)]
