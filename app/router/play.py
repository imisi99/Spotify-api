from fastapi import APIRouter, Cookie, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette import status
from sqlalchemy import desc, asc
from .user import refresh_access_token
from ..schemas.config import db_dependency, user_dependency, check_expired_token
from ..schemas.model import *
from ..schemas.user_schemas import *
import requests
import logging

play = APIRouter()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@play.get('/search')
async def search_tracks_spotify(name: str,
                                request: Request,
                                user: user_dependency,
                                token: str | None = Cookie(None, alias="access_token")):
    if not token or not user:
        return RedirectResponse(url='/user/login')
    if check_expired_token(token):
        await refresh_access_token(request, url='/play/search')

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
                         request: Request,
                         token: str | None = Cookie(None, alias="access_token")):
    if not user or not token:
        return RedirectResponse(url='/user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/playlists/search')

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
        return {'message': 'No playlist with that keyword, maybe you can create one'}

    return {'playlists': playlist}


@play.get('/search/playlist')
async def get_playlist_id(payload: AlterPlaylist,
                          user: user_dependency,
                          db: db_dependency):
    if not user:
        return RedirectResponse(url='/user/login')
    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Playlist not found')
    return playlist


@play.post('/create')
async def create_playlist(payload: PlaylistCreate,
                          user: user_dependency,
                          db: db_dependency,
                          request: Request,
                          token: str | None = Cookie(None, alias="access_token"),
                          ):
    if not user or not token:
        return RedirectResponse(url='/user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/create')

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Failed to verify access token')

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
            user_id=user.id,
        )

        new.users.append(user)

        add_user = db.query(UserModel).filter(UserModel.id == user.id).first()
        if not add_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized user')
        add_user.created_playlist += 1

        db.add(new)
        db.commit()

        logging.info(f"User with id: {user.id} has created a public playlist with id: {playlist_id}")

        return {'message': 'Playlist created successfully'}

    else:
        raise HTTPException(status_code=playlist.status_code, detail=f'Failed to create playlist: {playlist.json()}')


@play.post('/create/private')
async def create_playlist_private(
        payload: PlaylistPrivateCreate,
        user: user_dependency,
        db: db_dependency,
        request: Request,
        token: str | None = Cookie(None, alias="access_token")):
    if not token or not user:
        return RedirectResponse(url='user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/create/private')

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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Failed to verify access token')

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
            user_id=user.id,
        )

        add_user = db.query(UserModel).filter(UserModel.id == user.id).first()
        if not add_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized user')
        add_user.created_playlist += 1

        new.users.append(user)

        db.add(new)
        db.commit()

        logging.info(f"User with id: {user.id} has created a private playlist with id: {playlist_id}")

        return {'message': 'Playlist created successfully'}

    else:
        raise HTTPException(status_code=playlist.status_code, detail=f'Failed to create playlist {playlist.json()}')


@play.put('/make_public')
async def private_to_public(payload: AlterPlaylist,
                            user: user_dependency,
                            db: db_dependency,
                            request: Request,
                            token: str | None = Cookie(None, alias="access_token")):
    if not user or not token:
        return RedirectResponse(url='user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/make_public')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={
            'Authorization': f'Bearer {token}'
        }
    )

    if user_info.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Failed to verify access token')

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Playlist not found')

    playlist_id = playlist.id
    playlist_update = requests.put(
        f'https://api.spotify.com/v1/playlists/{playlist_id}/',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'},
        json={'collaborative': True,
              'public': False}
    )

    if playlist_update.status_code != 200:
        raise HTTPException(status_code=playlist_update.status_code, detail=playlist_update.json())

    return {'message': 'Playlist can now be edited by everyone'}


@play.put('/make_private')
async def public_to_private(payload: AlterPlaylist,
                            user: user_dependency,
                            db: db_dependency,
                            request: Request,
                            token: str | None = Cookie(None, alias="access_token")):
    if not user or not token:
        return RedirectResponse(url='/user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/make_private')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={'Authorization': f'Bearer {token}'}
    )

    if user_info.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Failed to verify access token')

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    if not playlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Playlist not found')
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

    return {'message': 'Playlist can now be edited by you only'}


@play.put('/alter')
async def alter_playlist(payload: AddTrack,
                         user: user_dependency,
                         db: db_dependency,
                         request: Request,
                         token: str | None = Cookie(None, alias="access_token")):
    if not user or not token:
        return RedirectResponse(url='/user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/alter')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={'Authorization': f'Bearer {token}'}
    )

    if user_info.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Failed to verify access token')

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    collab = requests.get(
        f'https://api.spotify.com/v1/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    if collab.status_code != 200:
        raise HTTPException(status_code=collab.status_code, detail=collab.json())

    if not collab.json().get('collaborative'):
        if playlist.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='You can not contribute to this playlist')

    track_id = [f'spotify:track:{track}' for track in payload.track_id if len(track) == 22]
    if len(track_id) == 0:
        return {"message": "No track was specified!"}

    add_track = requests.post(
        f'https://api.spotify.com/v1/playlists/{playlist.id}/tracks',
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json'
                 },
        json={'uris': track_id}
    )

    if add_track.status_code == 201:
        time = requests.get(
            f'https://api.spotify.com/v1/playlists/{playlist.id}',
            headers={'Authorization': f'Bearer {token}'}
        )

        if time.status_code != 200:
            raise HTTPException(status_code=time.status_code, detail=time.json())

        time_sum = sum(item['track']['duration_ms'] for item in time.json()['tracks']['items'])
        time_sum = time_sum // 1000

        playlist.time = time_sum
        exist = (db.query(playlist_users).filter(playlist_users.c.playlist_id == playlist.id).
                 filter(playlist_users.c.user_id == user.id).first())
        if not exist:
            playlist.users.append(user)
        db.add(playlist)
        db.commit()

        logging.info(f"The playlist: {playlist.id} has been altered by user: {user.id}")

        return {'message': 'Track added to playlist successfully'}
    else:
        raise HTTPException(status_code=add_track.status_code, detail=add_track.json())


@play.put('/alter/d')
async def remove_tracks(payload: AddTrack,
                        user: user_dependency,
                        db: db_dependency,
                        request: Request,
                        token: str | None = Cookie(None, alias="access_token")):
    if not user or not token:
        return RedirectResponse(url='user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/alter/d')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    if user_info.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to verify access token")

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    if not playlist:
        return {'message': 'Playlist not found!'}

    track_id = [{'uri': f'spotify:track:{track}'} for track in payload.track_id if len(track) == 22]
    if not track_id:
        return {'message': 'No valid track found'}

    collab = requests.get(
        f'https://api.spotify.com/v1/playlists/{payload.id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    if not collab.json().get('collaborative'):
        if playlist.user_id != user.id:
            return {'message': 'This playlist is private'}

    remove_track = requests.delete(
        f'https://api.spotify.com/v1/playlists/{playlist.id}/tracks',
        headers={'Authorization': f'Bearer {token}',
                 'Content-Type': 'application/json'
                 },
        json={'tracks': track_id}
    )

    if remove_track.status_code != 200:
        raise HTTPException(status_code=remove_track.status_code,
                            detail=remove_track.json())

    time = requests.get(
        f'https://api.spotify.com/v1/playlists/{playlist.id}',
        headers={'Authorization': f'Bearer {token}'}
    )

    if time.status_code != 200:
        raise HTTPException(status_code=time.status_code, detail=time.json())

    time_sum = sum(item['track']['duration_ms'] for item in time.json()['tracks']['items'])
    time_sum = time_sum // 1000

    playlist.time = time_sum
    exist = (db.query(playlist_users).filter(playlist_users.c.playlist_id == playlist.id).
             filter(playlist_users.c.user_id == user.id).first())
    if not exist:
        playlist.users.append(user)
    db.add(playlist)
    db.commit()

    logging.info(f"The playlist: {playlist.id} has been altered by user: {user.id}")

    return {'message': 'Tracks removed from the playlist successfully'}


@play.delete('/remove/track')
async def remove_playlist(payload: AlterPlaylist,
                          user: user_dependency,
                          db: db_dependency,
                          request: Request,
                          token: str | None = Cookie(None, alias="access_token")):
    if not user or not token:
        return RedirectResponse(url='/user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/remove/track')

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    if not playlist:
        return {'message': 'Playlist not found'}

    collab = requests.get(f'https://api.spotify.com/v1/playlists/{playlist.id}',
                          headers={'Authorization': f'Bearer {token}'})

    if not collab:
        raise HTTPException(status_code=collab.status_code, detail=collab.json())

    if not collab.json().get('collaborative'):
        if user.id != playlist.user_id:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this playlist")

    remove = requests.delete(f'https://api.spotify.com/v1/playlists/{playlist.id}/followers',
                             headers={'Authorization': f'Bearer {token}'}
                             )

    if remove.status_code == 404:
        add_user = db.query(UserModel).filter(UserModel.id == user.id).first()
        if not add_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized user')
        add_user.created_playlist -= 1

        db.delete(playlist)
        db.commit()
        return {'message': 'Playlist already deleted on spotify'}
    elif remove.status_code == 200:
        add_user = db.query(UserModel).filter(UserModel.id == user.id).first()
        if not add_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized user')
        add_user.created_playlist -= 1

        db.delete(playlist)
        db.commit()

        logging.info(f"The playlist: {playlist.id} has been deleted by user: {user.id}")

        return {'message': 'Playlist deleted successfully'}
    else:
        raise HTTPException(status_code=remove.status_code, detail=remove.json())


@play.get('/listen')
async def listen(payload: Listen,
                 user: user_dependency,
                 db: db_dependency,
                 request: Request,
                 token: str | None = Cookie(None, alias="access_token")):
    if not user or not token:
        return RedirectResponse(url='/user/login')
    if check_expired_token(token):
        return await refresh_access_token(request, url='/play/listen')

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={'Authorization': f'Bearer {token}'}
    )

    if user_info.status_code != 200:
        raise HTTPException(status_code=user_info.status_code, detail='Failed to verify access token')

    playlist = requests.get(
        f'https://api.spotify.com/v1/playlists/{payload.playlist_id}',
        headers={'Authorization': f'Bearer {token}'}
    )

    if playlist.status_code != 200:
        raise HTTPException(status_code=playlist.status_code, detail=playlist.json())

    plays = db.query(Playlist).filter(Playlist.id == payload.playlist_id).first()
    if plays:
        plays.plays += 1

        db.add(plays)
        db.commit()

    return {
        "access_token": token,
        "playback_url_spotify": f'https://open.spotify.com/playlist/{payload.playlist_id}',
        "playlist_uri": f"spotify:playlist:{payload.playlist_id}"
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

    db.add(playlist)
    db.commit()


@play.get('/discussion', response_model=DiscussionResponse)
async def get_discussion(payload: AlterPlaylist,
                         user: user_dependency,
                         db: db_dependency):
    if not user:
        return RedirectResponse(url='/user/login')

    discussion = db.query(Discussion).filter(Discussion.playlist_id == payload.id).order_by(
        asc(Discussion.time_stamp)).all()

    if not discussion:
        return {'message': 'No comments available for the playlist be the first to comment'}

    comments = []
    for comment in discussion:
        discuss = DiscussionReturn(
            comment=comment.comment,
            time=comment.time_stamp
        )

        comments.append(discuss)

    return {'comments': comments}


@play.post('/start_discussion')
async def start_discussion(payload: Comment,
                           user: user_dependency,
                           db: db_dependency
                           ):
    if not user:
        return RedirectResponse(url='/user/login')
    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()
    if not playlist:
        return {'message': 'Playlist not found'}

    new_chat = Discussion(
        user_id=user.id,
        playlist_id=playlist.id,
        comment=payload.comment
    )

    playlist.comments += 1
    db.add(new_chat)
    db.commit()


@play.get('/rating')
async def get_ratings(payload: AlterPlaylist,
                      user: user_dependency,
                      db: db_dependency):
    if not user:
        return RedirectResponse(url='/user/login')

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()

    if not playlist:
        return {'message': 'Playlist not found'}
    return {'message': f'This playlist has a rating of {playlist.rating}'}


@play.put('/alter/r')
async def add_ratings(payload: Rate,
                      user: user_dependency,
                      db: db_dependency):
    if not user:
        return RedirectResponse(url='/user/login')

    playlist = db.query(Playlist).filter(Playlist.id == payload.id).first()

    if not playlist:
        return {'message': 'Playlist not found'}
    if 5.0 < payload.rating or payload.rating < 0.0:
        return {'message': 'Please enter a valid rating on the scale of 0.0 to 5.0'}

    existing_rating = db.query(Rating).filter(Rating.user_id == user.id).filter(
        Rating.playlist_id == payload.id).first()
    if not existing_rating:
        new = Rating(
            user_id=user.id,
            playlist_id=playlist.id,
            rating=payload.rating
        )

        db.add(new)
    if existing_rating:
        existing_rating.rating = payload.rating
    db.commit()

    count = db.query(Rating).filter(Rating.playlist_id == payload.id).count()
    avg = db.query(func.sum(Rating.rating)).scalar()
    avg /= count
    playlist.rating = avg

    db.add(playlist)
    db.commit()


@play.get('/most_vote')
async def get_most_vote(user: user_dependency,
                        db: db_dependency):
    if not user:
        return RedirectResponse(url='/user/login')

    rate = db.query(Playlist).order_by(Playlist.rating.desc()).first()
    plays = db.query(Playlist).order_by(Playlist.plays.desc()).first()

    def compute_score(rating, played, rw=0.85, pw=0.15):
        return (rating * rw) + (played * pw)

    highest_rating = compute_score(rate.rating, rate.plays)
    highest_play = compute_score(plays.rating, plays.plays)

    if highest_rating > highest_play:
        playlist = rate
    else:
        playlist = plays

    return {
        'top_playlist': {
            'id': playlist.id,
            'name': playlist.name,
            'rating': playlist.rating,
            'plays': playlist.plays,
            'score': max(highest_rating, highest_play)
        }
    }
