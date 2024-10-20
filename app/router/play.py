from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import RedirectResponse
from starlette import status
from ..schemas.config import db_dependency, user_dependency
from ..schemas.model import *
import requests

play = APIRouter()


# Users should be able to create and contribute to a playlist
@play.post('/create')
async def create_playlist(name: str,
                          description: str,
                          user: user_dependency,
                          db: db_dependency,
                          public: bool = True,
                          collaborative: bool = True,
                          token: str | None = Cookie(None, alias="access_token"),
                          ):
    if not user:
        return RedirectResponse(url='/user/login')
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
        user_id = user_data.get('id')
    else:
        raise HTTPException(status_code=user_info.status_code, detail='failed to fetch user info')

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User Id not found')

    playlist = requests.post(
        f'https://api.spotify.com/v1/users/{user_id}/playlists',
        headers={
            'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={'name': name, 'description': description, 'public': public, 'collaborative': collaborative}
    )

    if playlist.status_code == 201:
        new = Playlist(
            name=name,
            username=user.get('username'),
            user_id=user.get('id')
        )

        db.add(new)
        db.commit()
        return {'message': f'Playlist created successfully {playlist.json()}'}

    else:
        raise HTTPException(status_code=playlist.status_code, detail='failed to create playlist')


@play.post('/create/private')
async def create_playlist_private(user: user_dependency,
                                  db: db_dependency,
                                  name: str,
                                  description: str,
                                  public: bool = True,
                                  collaborative: bool = False,
                                  token: str | None = Cookie(None, alias="access_token")):
    if not token:
        return RedirectResponse(url='user/login')
    if not user:
        return RedirectResponse(url='user/login')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={
            'Authorization': f'Bearer {token}'
        }
    )

    if user_info.status_code == 200:
        user_data = user_info.json()
        user_id = user_data.get('id')
    else:
        raise HTTPException(status_code=user_info.status_code, detail='failed to fetch user info')

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to fetch user Id')

    playlist = requests.post(
        f'https://api.spotify.com/v1/users/{user_id}/playlists',
        headers={
            'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={'name': name, 'description': description, 'public': public, 'collaborative': collaborative}
    )

    if playlist.status_code == 200:
        new = Playlist(
            name=name,
            username=user.get('username'),
            user_id=user.get('id')
        )

        db.add(new)
        db.commit()
        return {'message': f'Playlist created successfully {playlist.json()}'}

    else:
        raise HTTPException(status_code=playlist.status_code, detail=playlist.json())


@play.put('/make_public')
async def private_to_public(name: str,
                            user: user_dependency,
                            db: db_dependency,
                            token: str | None = Cookie(None, alias="access_token")):

    if not user:
        return RedirectResponse(url='user/login')
    if not token:
        return RedirectResponse(url='user/login')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={
            'Authorization': f'Bearer {token}'
        }
    )

    if user_info.status_code == 200:
        user_data = user_info.json()
        user_id = user_data.get('id')

        if user_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Failed to fetch user id')
    else:
        raise HTTPException(status_code=user_info.status_code, detail=user_info.json())

    playlist_update = requests.put(
        f'https://api.spotify.com/v1/users/{user_id}/playlists/',
        headers={
            'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={}
    )


@play.put('/make_private')
async def public_to_private():
    pass


@play.put('/alter')
async def alter_playlist():
    pass


# Users should be able to listen to music even if they are not logged-in
@play.get('/listen')
async def listen():
    pass


# Users should be able to discuss playlist and the likes
@play.get('/discussion')
async def get_discussion():
    pass


@play.post('/start_discussion')
async def start_discussion():
    pass


@play.put('/alter_discussion')
async def make_discussion():
    pass
