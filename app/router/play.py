from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import RedirectResponse
from starlette import status
from sqlalchemy import desc
from ..schemas.config import db_dependency, user_dependency
from ..schemas.model import *
from ..schemas.user_schemas import *
import requests

play = APIRouter()


# Users should be able to create and contribute to a playlist

@play.get('/search')
async def search_tracks_spotify(name: str,
                                token: str | None = Cookie(None, alias="access_token")):
    if not token:
        return RedirectResponse(url='/user/login')

    search_response = requests.get(
        'https://api.spotify.com/v1/search',
        headers={'Authorization': f'Bearer {token}'},
        params={
            'q': name,
            'type': 'track',
            'limit': 15
        }
    )
    if search_response.status_code == 200:
        search_data = search_response.json()

        tracks = [
            {
                'track_id': item['id'],
                'name': item['name'],
                'artist': item['artists'][0]['name'],
                'album': item['album']['name']
            }
            for item in search_data['tracks']['items']
        ]
        return {'tracks': tracks}

    else:
        raise HTTPException(status_code=search_response.status_code, detail=search_response.json())


@play.get('/playlists/search', response_model=PlaylistResponse)
async def find_playlists(name: str,
                         user: user_dependency,
                         db: db_dependency,
                         token: str | None = Cookie(None, alias="access_token")):
    if not user:
        return RedirectResponse(url='/user/login')
    if not token:
        return RedirectResponse(url='/user/login')

    playlist_search = db.query(Playlist).filter(
        (Playlist.name.ilike(f"%{name}%")) |
        (func.similarity(Playlist.name, name) > 0.2)
    ).order_by(
        desc(func.similarity(Playlist.name, name))
    ).all()

    playlist = []

    for item in playlist_search:
        collab = [user.username for user in item.users]

        playlist_data = PlaylistReturn(
            name=item.name,
            username=collab,
            genre=item.genre,
            likes=item.likes,
            plays=item.plays,
            dislike=item.dislike,
            rating=item.rating,
            comments=item.comments,
        )

        playlist.append(playlist_data)

    if not playlist_search:
        raise HTTPException(status_code=404, detail='No playlist found, try using a different keyword')

    return {'playlists': playlist}


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
            user_id=user.id
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
            user_id=user.id
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

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail='No playlist with that name')
    playlist_id = playlist.id
    playlist_update = requests.put(
        f'https://api.spotify.com/v1/playlists/{playlist_id}/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'},
        json={'collaborative': True,
              'public': True}
    )

    if playlist_update.status_code != 200:
        raise HTTPException(status_code=playlist_update.status_code, detail=playlist_update.json())

    return {'message': 'Playlist can now be edited by everyone'}


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
        headers={'Authorization': f'Bearer {token}'}
    )

    if user_info.status_code != 200:
        raise HTTPException(status_code=user_info.status_code, detail=user_info.json())

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail='No playlist with that name')
    playlist_id = playlist.id

    playlist_update = requests.put(
        f'https://api.spotify.com/v1/playlists/{playlist_id}/',
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json'
                 },
        json={'collaborative': False,
              'public': False}
    )

    if playlist_update.status_code != 200:
        raise HTTPException(status_code=playlist_update.status_code, detail=playlist_update.json())

    return {'message': 'Playlist can now be edited by the owner only'}


@play.put('/alter')
async def alter_playlist(payload: AddTrack,
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
        headers={'Authorization': f'Bearer {token}'}
    )

    if user_info.status_code != 200:
        raise HTTPException(status_code=user_info.status_code, detail=user_info.json())

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    collab = requests.get(
        f'https://api.spotify.com/v1/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    if collab.status_code != 200:
        raise HTTPException(status_code=collab.status_code, detail=collab.json())

    if not collab.json().get('collaborative'):
        if playlist.user_id != user.id:
            raise HTTPException(status_code=403, detail='You are not the owner of this playlist')

    add_track = requests.post(
        f'https://api.spotify.com/v1/playlists/{playlist.id}/tracks',
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json'
                 },
        json={'uris': payload.track_id}
    )

    if add_track.status_code == 201:
        playlist.users.append(user)
        db.add(playlist)
        db.commit()
        return {'message': 'Track added to the playlist successfully'}
    else:
        raise HTTPException(status_code=add_track.status_code, detail=add_track.json())


# Users should be able to listen to music even if they are not logged-in
@play.get('/listen')
async def listen(payload: Listen,
                 user: user_dependency,
                 token: str | None = Cookie(None, alias="access_token")):
    if not user:
        return RedirectResponse(url='/user/login')
    if not token:
        return RedirectResponse(url='/user/login')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={'Authorization': f'Bearer {token}'}
    )

    if user_info.status_code != 200:
        raise HTTPException(status_code=user_info.status_code, detail='Failed to verify token')

    playlist = requests.get(
        f'https://api.spotiify.com/v1/playlists/{payload.playlist_id}',
        headers={'Authorization': f'Bearer {token}'}
    )

    if playlist.status_code != 200:
        raise HTTPException(status_code=playlist.status_code, detail='Playlist not found')

    return {
        "access_token": token,
        "playback_url": f'https://open.spotify.com/playlist/{payload.playlist_id}',
    }


# Users should be able to like, dislike and rate playlist
@play.put('/likes')
async def like_playlist(payload: AlterPlaylist,
                        user: user_dependency,
                        db: db_dependency):
    if not user:
        return RedirectResponse(url='/user/login')

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()

    if not playlist:
        raise HTTPException(status_code=404, detail='No playlist with that name')

    if user in playlist.liked_by:
        return
    playlist.liked_by.append(user)
    playlist.likes += 1

    if user in playlist.disliked_by:
        playlist.disliked_by.remove(user)
        playlist.dislike -= 1

    db.add(playlist)
    db.commit()


@play.put('/dislike')
async def dislike_playlist(payload: AlterPlaylist,
                           user: user_dependency,
                           db: db_dependency):
    if not user:
        return RedirectResponse(url='/user/login')

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()

    if not playlist:
        raise HTTPException(status_code=404, detail='No playlist with that name')

    if user in playlist.disliked_by:
        return

    playlist.disliked_by.append(user)
    playlist.dislike += 1

    if user in playlist.liked_by:
        playlist.liked_by.remove(user)
        playlist.likes -= 1

    db.add(Playlist)
    db.commit()


# Users should be able to contribute to a playlist
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
