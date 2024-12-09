from pydantic import BaseModel
from typing import Optional, List


class Token(BaseModel):
    access_token: str
    token_type: str


class PlaylistCreate(BaseModel):
    name: str
    description: str
    public: bool = False
    collaborative: bool = True


class PlaylistPrivateCreate(BaseModel):
    name: str
    description: str
    public: bool = False
    collaborative: bool = False


class AlterPlaylist(BaseModel):
    id: str


class PlaylistReturn(BaseModel):
    name: str
    username: List[str]
    genre: Optional[str]
    likes: int
    dislike: int
    plays: int
    rating: Optional[float]
    comments: int


class DiscussionReturn(BaseModel):
    comment: str
    time: str


class DiscussionResponse(BaseModel):
    comments: List[DiscussionReturn]


class PlaylistResponse(BaseModel):
    playlists: List[PlaylistReturn]


class AddTrack(BaseModel):
    track_id: List[str]
    id: str


class Listen(BaseModel):
    playlist_id: str


class Rate(BaseModel):
    id: str
    rating: float


class Comment(BaseModel):
    id: str
    comment: str
