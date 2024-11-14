from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str


class PlaylistCreate(BaseModel):
    name: str
    description: str
    public: bool = True
    collaborative: bool = True


class PlaylistPrivateCreate(BaseModel):
    name: str
    description: str
    pubic: bool = False
    collaborative: bool = False


class AlterPlaylist(BaseModel):
    name: str


class PlaylistReturn(BaseModel):
    name: str
    username: list[str]
    genre: Optional[str] = None
    likes: int
    dislike: int
    plays: int
    rating: Optional[float] = None
    comments: int


class AddTrack(BaseModel):
    track_id: list[str]
    playlist_name: str
