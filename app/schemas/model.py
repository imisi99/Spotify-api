from .database import data
from sqlalchemy import Column, String, Integer, ForeignKey, Float, DateTime, UniqueConstraint, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

playlist_users = Table(
    'playlist_users', data.metadata,
    Column('playlist_id', String, ForeignKey('playlist.id', ondelete="CASCADE"), primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True)
)

playlist_likes = Table(
    'playlist_likes', data.metadata,
    Column('playlist_id', String, ForeignKey('playlist.id', ondelete="CASCADE"), primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True)
)

playlist_dislikes = Table(
    'playlist_dislikes', data.metadata,
    Column('playlist_id', String, ForeignKey('playlist.id', ondelete="CASCADE"), primary_key=True),
    Column('user_id', Integer, ForeignKey('user.id', ondelete="CASCADE"), primary_key=True)
)


class UserModel(data):
    __tablename__ = 'user'

    id = Column(Integer, index=True, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    created_playlist = Column(Integer, nullable=False, default=0)
    followers = Column(Integer, nullable=False, default=0)
    following = Column(Integer, nullable=False, default=0)
    level = Column(String, nullable=False, default="rookie")

    playlists = relationship('Playlist', secondary=playlist_users, back_populates='user')

    ratings = relationship('Rating', back_populates='user')
    comments = relationship('Discussion', back_populates='user')

    liked_playlists = relationship('Playlist', secondary=playlist_likes, back_populates='liked_by')
    disliked_playlists = relationship('Playlist', secondary=playlist_dislikes, back_populates='disliked_by')


class Playlist(data):
    __tablename__ = "playlist"

    id = Column(String, primary_key=True)
    name = Column(String(50), nullable=False, unique=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    genre = Column(String, index=True, nullable=True)
    time = Column(Integer, nullable=True, default=0)
    likes = Column(Integer, nullable=False, default=0)
    dislike = Column(Integer, nullable=False, default=0)
    plays = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=True, default=0.0)
    comments = Column(Integer, nullable=False, default=0)

    users = relationship('UserModel', secondary=playlist_users, back_populates='playlists')

    comments_relationship = relationship('Discussion', back_populates='playlist')
    ratings = relationship('Rating', back_populates='playlist')

    liked_by = relationship('UserModel', secondary=playlist_likes, back_populates='liked_playlists')
    disliked_by = relationship('UserModel', secondary=playlist_dislikes, back_populates='disliked_playlists')


class Discussion(data):
    __tablename__ = "comments"

    id = Column(Integer, index=True, primary_key=True)
    playlist_id = Column(String, ForeignKey("playlist.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    time_stamp = Column(DateTime, nullable=False, default=func.now())
    comment = Column(String(100), nullable=False)

    user = relationship('UserModel', back_populates='comments')
    playlist = relationship('Playlist', back_populates='comments_relationship')


class Rating(data):
    __tablename__ = "rating"

    id = Column(Integer, index=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    playlist_id = Column(String, ForeignKey("playlist.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'playlist_id', name='unique_user_playlist'),)

    user = relationship('UserModel', back_populates='ratings')
    playlist = relationship('Playlist', back_populates='ratings')


class Following(data):
    __tablename__ = "follows"

    id = Column(Integer, index=True, primary_key=True)
    following = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    follower = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)


class State(data):
    __tablename__ = 'state'

    id = Column(Integer, index=True, primary_key=True)
    state = Column(String, nullable=False)
