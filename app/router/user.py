from fastapi import APIRouter, HTTPException, Response, Request, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from starlette import status
from dotenv import load_dotenv
from ..schemas.config import db_dependency, user_dependency, authentication, welcome_email
from ..schemas.user_schemas import *
from ..schemas.model import UserModel
from datetime import timedelta
import string
import random
import urllib.parse
import requests
import os
import base64

load_dotenv()

user = APIRouter()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")


@user.get("/login")
def login(request: Request):
    state = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    params = {
        'state': state,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'user-read-private user-read-email user-library-read user-library-modify playlist-read-private playlist-modify-private',

    }
    request.session["state"] = state
    url = f'https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}'
    return RedirectResponse(url)


@user.get("/callback", response_model=Token)
def callback(request: Request, db: db_dependency):
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    error = request.query_params.get('error')

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    valid_state = request.session.get('state')
    if valid_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid State')

    token_request = requests.post(
        'https://accounts.spotify.com/api/token',
        data={
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        },
        headers={
            'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
            'content-type': 'application/x-www-form-urlencoded'
        }
    )

    if token_request.status_code == 200:
        token_info = token_request.json()
        request.session["access_token"] = token_info['access_token']

        token = request.session.get('access_token')

        user_info = requests.get(
            'https://api.spotify.com/v1/me',
            headers={
                'Authorization': f'Bearer {token}'
            }
        )

        if user_info.status_code == 200:
            user_data = user_info.json()

            existing_user = db.query(UserModel).filter(UserModel.email == user_data.get('email')).first()
            if not existing_user:
                new_user = UserModel(
                    username=user_data.get('display_name'),
                    email=user_data.get('email')
                )
                db.add(new_user)
                db.commit()

                if welcome_email(user_data.get('email'), user_data.get('display_name')):
                    pass
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unauthorized user')

        else:
            raise HTTPException(status_code=user_info.status_code, detail='failed to fetch user info')

        get_user_data = db.query(UserModel).filter(UserModel.email == user_data.get('email')).first()
        jwt_token = authentication(get_user_data.id, get_user_data.username, timedelta(days=30))

        response = JSONResponse(content={
            'message': 'User successfully logged in.'
        })

        response.set_cookie(
            key='jwt_token',
            value=jwt_token,
            httponly=True,
            max_age=60 * 60 * 24 * 14,
            secure=True,
            samesite='lax'
        )
        response.set_cookie(
            key='access_token',
            value=token,
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            secure=True,
            samesite='lax'
        )

        return response
    else:
        raise HTTPException(status_code=token_request.status_code, detail='failed to fetch access token')


@user.get('/profile')
def get_user_profile(db: db_dependency, user: user_dependency, token: str | None = Cookie(None, alias="access_token")):
    if not user:
        return RedirectResponse(url='user/login')
    if not token:
        return RedirectResponse(url='/user/login')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={
            'Authorization': f'Bearer {token}'
        }
    )

    if user_info.status_code == 200:
        user_data = user_info.json()
        email = user_data.get('email')
        if email is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        user_db = db.query(UserModel).filter(UserModel.email == email).first()
        if user_db is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if user_db.username != user_data.get('display_name'):
            user_db.username = user_data.get('display_name')
            db.add(user_db)
            db.commit()

        profile = {
            'username': user_db.username,
            'email': user_db.email,
            'followers': user_db.followers,
            'following': user_db.following,
            'level': user_db.level,
            'playlists': user_db.created_playlist

        }

        return profile
    else:
        raise HTTPException(status_code=user_info.status_code, detail='failed to fetch user info')


@user.get('/logout')
def logout(response: Response):
    response.delete_cookie('jwt_token')
    response.delete_cookie('access_token')
    return RedirectResponse(url='/')
