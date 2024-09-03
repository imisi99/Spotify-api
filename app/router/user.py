from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette import status
from dotenv import load_dotenv
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


@user.get("/callback")
def callback(request: Request):
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
        return RedirectResponse(url='/dashboard')
    else:
        raise HTTPException(status_code=token_request.status_code, detail='failed to fetch access token')


@user.get('/profile')
def get_user(request: Request):
    token = request.session.get('access_token')
    if not token:
        return RedirectResponse(url='/user/login')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={
            'Authorization': f'Bearer {token}'
        }
    )

    if user_info.status_code == 200:
        return user_info.json()
    else:
        raise HTTPException(status_code=user_info.status_code, detail='failed to fetch user info')


@user.get('/logout')
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='/')
