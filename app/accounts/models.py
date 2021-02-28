from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException
from datetime import timedelta, datetime
from passlib.context import CryptContext

from . import schemas
from ..config.db import db
from ..config.config import Envs
from ..tables.users import users
from ..tables.roles import roles


class User:
    db = db
    users = users
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated=['auto'])


    @classmethod
    async def register(cls, user: schemas.UserRegisterRequest) -> schemas.UserRegisterResponse:
        try:
            user.password = pwd_context.hash(user.password)
            query = cls.users.insert().values(**user.dict())
            user_id = await cls.db.execute(db)
            new_user_response = schemas.UserRegisterResponse(id=user_id)
            return new_user_response
        except:
            raise HTTPException(status_code=400, detail='Email has been registered')


    @classmethod
    async def login(cls, user: schemas.UserLoginRequest) -> schemas.UserLoginResponse:
        try:
            authenticated_user = await cls.authenticate_user(user.email, user.password)
            token_expires = timedelta(hours=Envs.ACCESS_TOKEN_EXPIRE_HOURS)
            jwt_token = cls.create_access_token({'sub': authenticated_user.email}, token_expires)
            return schemas.UserLoginResponse(token_type='Bearer', access_token=jwt_token)
        except:
            raise HTTPException(status_code=400, detail='Wrong email or password')


    @classmethod
    async def authenticate_user(cls, email: str, password: str):
        try:
            print('email', email)
            query = cls.users.select().where(users.c.email == email)
            user = await cls.db.fetch_one(query)
            verified = cls.pwd_context.verify(password, user.password)
            if verified:
                return user
            raise HTTPException(status_code=400, detail='Wrong email or password')
        except:
            raise HTTPException(status_code=400, detail='User not found')


    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(hours=1)
        to_encode.update({'exp': expire})
        encoded_jwt = jwt.encode(to_encode, Envs.SECRET_KEY, algorithm=Envs.ALGORITHM)
        return encoded_jwt
