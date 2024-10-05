from fastapi import APIRouter

play = APIRouter()


# Users should be able to create and contribute to a playlist
@play.post()
async def create_playlist():
    pass


@play.post()
async def create_playlist_private():
    pass


@play.put()
async def private_to_public():
    pass


@play.put()
async def public_to_private():
    pass


@play.put()
async def alter_playlist():
    pass


# Users should be able to listen to music even if they are not logged-in
@play.get()
async def listen():
    pass


# Users should be able to discuss playlist and the likes
@play.get()
async def get_discussion():
    pass


@play.post()
async def start_discussion():
    pass


@play.put()
async def make_discussion():
    pass
