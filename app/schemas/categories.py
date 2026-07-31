from pydantic import BaseModel, ConfigDict, Field

from app.schemas.posts import PostShortResponse


class CategoryAdd(BaseModel):
    title: str


class Category(CategoryAdd):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CategoryPatch(BaseModel):
    title: str | None = Field(None)


class CategoryShortResponse(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class CategoryResponse(BaseModel):
    id: int
    title: str
    posts: list[PostShortResponse] = []

    model_config = ConfigDict(from_attributes=True)
