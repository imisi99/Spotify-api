import os
from fastapi.responses import RedirectResponse
from .database import begin
from .model import UserModel
from jose import JWTError, jwt
from typing import Annotated
from fastapi import Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from datetime import datetime
from starlette import status
from postmarker.core import PostmarkClient


def get_db():
    db = begin()
    try:
        yield db
    finally:
        db.close()


secret = os.getenv('SECRET')
Algorithm = os.getenv('ALGORITHM')
conf = os.getenv('FROM')
postmark = PostmarkClient(server_token=os.getenv('POSTMARK'))


def authentication(user_id: int, username: str, limit):
    encode = {'sub': username, 'id': user_id}
    exp = datetime.utcnow() + limit
    encode.update({'exp': exp})
    return jwt.encode(encode, secret, algorithm=Algorithm)


db_dependency = Annotated[Session, Depends(get_db)]


async def get_user(db: db_dependency, token: str | None = Cookie(None, alias="jwt_token")):
    if token is None:
        return RedirectResponse(url='/user/login')
    try:
        payload = jwt.decode(token, secret, algorithms=[Algorithm])
        user_id = payload.get('id')
        username = payload.get('sub')
        exp = payload.get('exp')

        exp = datetime.utcfromtimestamp(exp)

        if user_id is None or username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid Token, please login again")
        if exp and datetime.utcnow() > exp:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZEDT,
                                detail="Session Expired, please login again")

        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"An error occurred as {e}")


def welcome_email(user_email, user_firstname):
    response = postmark.emails.send(
        From=conf,
        To=user_email,
        Subject='Welcome To Dashie',
        HtmlBody=(f'''
    <div style="font-family: Arial, sans-serif; color: #333; background-color: #f0f4f8; padding: 20px; border-radius: 10px; text-align: center;">
        <h3 style="color: #4caf50;">🎉 Hey, {user_firstname}! 🎉</h3>
        <p style="font-size: 15px;">
            We are pleased to have you onboard, Welcome to a great experience Buckle up cause listening to music has not been this fun.
        </p>
        <p style="font-size: 15px; margin-top: 10px;">
            We are streaming platform that allow for listeners like you to not only play music but also be able to share your experience with your friends by collaborating to create playlist together and so much more
        </p>
        <div style="margin-top: 15px;">
            <a href="https://spotify-dv92.onrender.com/user/login" style="text-decoration: none; background-color: #4caf50; color: green; padding: 10px 20px; border-radius: 5px; font-size: 15px;">Begin your journey</a>
        </div>
        <p style="font-size: 14px; color: #757575; margin-top: 20px;">
            Once again Welcome,<br/>
            <strong>Dashie</strong>
        </p>
    </div>
'''),
        TextBody=f'Hey {user_firstname},\n We are pleased to have you onboard, Welcome to a great experience Buckle up cause listening to music has not been this fun.\n We are streaming platform that allow for listeners like you to not only play music but also'
                 f'be able to share your experience with your friends by collaborating to create playlist together and so much more.\n\n\n Once again Welcome to Dashie \n You can begin your journey here https://spotify-dv92.onrender.com/user/login',
        MessageStream='outbound'

    )

    if response['ErrorCode'] == 0:
        return True
    else:
        return False


user_dependency = Annotated[Session, Depends(get_user)]
