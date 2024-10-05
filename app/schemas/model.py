from .database import data
from sqlalchemy import Column, String, Integer


class UserModel(data):
    __tablename__ = 'user'

    id = Column(Integer, index=True, primary_key=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)


class State(data):
    __tablename__ = 'state'

    id = Column(Integer, index=True, primary_key=True)
    state = Column(String, nullable=False)

