from .database import data
from sqlalchemy import Column, String, Integer, ForeignKey, Float, DateTime, UniqueConstraint


class UserModel(data):
    __tablename__ = 'user'

    id = Column(Integer, index=True, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    created_playlist = Column(Integer, nullable=False, default=0)
    followers = Column(Integer, nullable=False, default=0)
    following = Column(Integer, nullable=False, default=0)
    level = Column(String, nullable=False, default="rookie")


class Playlist(data):
    __tablename__ = "playlist"

    id = Column(Integer, index=True, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    username = Column(String, nullable=False)
    genre = Column(String, index=True, nullable=True)
    time = Column(Integer, nullable=True, default=0)
    likes = Column(Integer, nullable=False, default=0)
    dislike = Column(Integer, nullable=False, default=0)
    plays = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=True, default=0.0)
    comments = Column(Integer, nullable=False, default=0)


class Discussion(data):
    __tablename__ = "comments"

    id = Column(Integer, index=True, primary_key=True)
    playlist_id = Column(Integer, ForeignKey("playlist.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    time_stamp = Column(DateTime, nullable=False)
    comment = Column(String(100), nullable=False)


class Rating(data):
    __tablename__ = "rating"

    id = Column(Integer, index=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    playlist_id = Column(Integer, ForeignKey("playlist.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'playlist_id', name='unique_user_playlist'),)


class State(data):
    __tablename__ = 'state'

    id = Column(Integer, index=True, primary_key=True)
    state = Column(String, nullable=False)
