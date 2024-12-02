from pydantic import BaseModel
from typing import Optional, List


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
    username: List[str]
    genre: Optional[str]
    likes: int
    dislike: int
    plays: int
    rating: Optional[float]
    comments: int


class PlaylistResponse(BaseModel):
    playlists: List[PlaylistReturn]


class AddTrack(BaseModel):
    track_id: list[str]
    playlist_name: str


class Listen(BaseModel):
    playlist_id: str
