from fastapi import APIRouter
from ..schemas.config import db_dependency, user_dependency

play = APIRouter()


# Users should be able to create and contribute to a playlist
@play.post('/create')
async def create_playlist():
    pass


@play.post('/create/private')
async def create_playlist_private():
    pass


@play.put('/make_public')
async def private_to_public():
    pass


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
