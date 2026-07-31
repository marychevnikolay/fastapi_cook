from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List

from app.schemas.users import UserResponse


class CommentAddRequest(BaseModel):
    """Схема для создания комментария"""

    text: str = Field(
        ..., min_length=1, max_length=1000, description="Текст комментария"
    )
    parent_id: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"text": "Great post! Thanks for sharing.", "parent_id": None}
        }
    )


class CommentAdd(BaseModel):
    """Схема для сохранения комментария в БД"""

    post_id: int
    author_id: int
    text: str
    parent_id: Optional[int] = None


class CommentUpdateRequest(BaseModel):
    """Схема для обновления комментария"""

    text: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    """Схема для ответа с комментарием"""

    id: int
    text: str
    created_at: datetime
    post_id: int
    _id: int
    parent_id: Optional[int] = None

    # Данные автора
    author: Optional[UserResponse] = None

    # Ответы на комментарий
    replies: List["CommentResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# Для рекурсивных типов
CommentResponse.model_rebuild()


class CommentShortResponse(BaseModel):
    id: int
    text: str

    model_config = ConfigDict(from_attributes=True)
