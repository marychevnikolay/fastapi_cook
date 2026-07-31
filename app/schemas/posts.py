from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.comments import CommentShortResponse
from app.schemas.users import UserResponse


class PostAddRequest(BaseModel):
    title: str
    content: str
    photo: str | None = None
    category_id: int | None = None


class PostAdd(BaseModel):
    category_id: int | None = None
    author_id: int | None = None
    title: str
    content: str | None = None
    photo: str | None = None
    comments: list[str] | None = None


class Post(PostAdd):
    id: int
    author_id: int
    created_at: datetime  # ← Добавляем поле
    # updated_at: datetime  # ← Добавляем поле
    watched: int
    is_published: bool
    comments: list[str] | None = None

    model_config = ConfigDict(from_attributes=True)


class PostPatchRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    photo: str | None = None
    category_id: int | None = None


class PostPatch(BaseModel):
    category_id: int | None = None
    title: str | None = None
    content: str | None = None
    photo: str | None = None
    is_published: bool | None = None  # ← Добавляем возможность обновлять статус


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: UserResponse
    comment: list[CommentShortResponse] = []
    # update_at : datetime | None | None


class PostShortResponse(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)
