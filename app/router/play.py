from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import RedirectResponse
from starlette import status
from ..schemas.config import db_dependency, user_dependency
from ..schemas.model import *
from ..schemas.user_schemas import *
import requests

play = APIRouter()


# Users should be able to create and contribute to a playlist
@play.post('/create')
async def create_playlist(payload: PlaylistCreate,
                          user: user_dependency,
                          db: db_dependency,
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
        json=payload.model_dump()
    )

    if playlist.status_code == 201:
        playlist_data = playlist.json()
        playlist_id = playlist_data.get('id')
        new = Playlist(
            id=playlist_id,
            name=payload.name,
            username=user.get('username'),
            user_id=user.get('id')
        )

        db.add(new)
        db.commit()

        return {'message': 'Playlist created successfully'}

    else:
        raise HTTPException(status_code=playlist.status_code, detail=f'failed to create playlist: {playlist.json()}')


@play.post('/create/private')
async def create_playlist_private(
        payload: PlaylistPrivateCreate,
        user: user_dependency,
        db: db_dependency,
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
        json=payload.model_dump()
    )

    if playlist.status_code == 201:
        playlist_data = playlist.json()
        playlist_id = playlist_data.get('id')
        new = Playlist(
            id=playlist_id,
            name=payload.name,
            username=user.get('username'),
            user_id=user.get('id')
        )

        db.add(new)
        db.commit()

        return {'message': 'Playlist created successfully'}

    else:
        raise HTTPException(status_code=playlist.status_code, detail=playlist.json())


@play.put('/make_public')
async def private_to_public(payload: AlterPlaylist,
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

    if user_info.status_code != 200:
        raise HTTPException(status_code=user_info.status_code, detail=user_info.json())

    # getting playlist id from db

    playlist = db.query(Playlist).filter(Playlist.name == payload.name).first()
    if not playlist:
        raise HTTPException(status_code=404, detail='No playlist with that name')
    playlist_id = playlist.id

    playlist_update = requests.put(
        f'https://api.spotify.com/v1/users/playlists/{playlist_id}/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'},
        json={'public': True}
    )

    if playlist_update.status_code != 200:
        raise HTTPException(status_code=playlist_update.status_code, detail=playlist_update.json())

    return {'message': 'Playlist updated to public successfully'}


@play.put('/make_private')
async def public_to_private(payload: AlterPlaylist,
                            user: user_dependency,
                            db: db_dependency,
                            token: str | None = Cookie(None, alias="access_token")):
    if not user:
        return RedirectResponse(url='/user/login')
    if not token:
        return RedirectResponse(url='/user/login')

    # validating token with spotify
    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={f'Authorization: Bearer {token}'}
    )

    if user_info.status_code != 200:
        raise HTTPException(status_code=user_info.status_code, detail=user_info.json())

    playlist = db.query(Playlist).filter(Playlist.name == payload.name).first()
    if not playlist:
        raise HTTPException(status_code=404, detail='No playlist with that name')
    playlist_id = playlist.get('id')

    playlist_update = requests.put(
        f'https://api.spotify.com/v1/users/playlists/{playlist_id}/',
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json'
                 },
        json={'public': False}
    )

    if playlist_update.status_code != 200:
        raise HTTPException(status_code=playlist_update.status_code, detail=playlist_update.json())

    return {'message': 'Playlist updated to private successfully '}


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
