from pydantic import BaseModel


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