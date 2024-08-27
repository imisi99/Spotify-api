from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette import status
from dotenv import load_dotenv
from ..schemas.config import db_dependency
from ..schemas.model import State
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
redirect_uri = 'http://localhost:8000/callback'


@user.get("/login")
def login(db: db_dependency):
    state = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    params = {
        'state': state,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'response_type': 'code',
        'scope': 'user-read-private user-read-email user-library-read user-library-modify playlist-read-private playlist-modify-private',

    }
    db.add(State(state=state))
    db.commit()
    url = f'https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}'
    return RedirectResponse(url)


@user.get("/callback")
def callback(request: Request, db: db_dependency):
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    error = request.query_params.get('error')

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    db_state = db.query(State).filter(State.state == state).first()
    if not db_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid State')

    db.delete(db_state)
    db.commit()

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
        return {'access_token': token_info['access_token'], 'token_type': token_info['token_type']}
    else:
        raise HTTPException(status_code=token_request.status_code, detail='failed to fetch access token')

