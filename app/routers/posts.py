from typing import List
from fastapi_cache.decorator import cache
from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.routers.dependencies import DBManager, UserIdDep, PaginationDep, get_db
from app.schemas.posts import (
    PostAdd,
    PostAddRequest,
    PostPatchRequest,
    PostPatch,
    Post,
    PostResponse,
)

router = APIRouter(prefix="/posts", tags=["Посты"])


##вывод всех постов по всем категориям, авторам
@router.get("", response_model=List[Post])
@cache(expire=10)
async def get_posts(
    pagination: PaginationDep,
    category_id: int | None = None,
    search: str | None = None,
    author_id: int | None = None,
    is_published: bool = None,
    db: DBManager = Depends(get_db),
):

    filters = {}
    if category_id is not None:
        filters["category_id"] = category_id
    if author_id is not None:
        filters["author_id"] = author_id
    if is_published is not None:
        filters["is_published"] = is_published

    # Получаем посты
    posts = await db.posts.get_filtered(
        **filters,
        search=search,
        limit=pagination.per_page,
        offset=(pagination.page - 1) * pagination.per_page,
    )

    return posts


@router.get("/{post_id}/", response_model=Post)
@cache(expire=10)
async def get_post(post_id: int, db: DBManager = Depends(get_db)):
    """
    Получить пост по ID
    """
    post = await db.posts.get_one_or_none(id=post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # Увеличиваем счетчик просмотров
    await db.posts.increment_watched(post_id)
    await db.commit()

    return post


@router.post("")
async def create_post(
    user_id: UserIdDep,
    post_data: PostAddRequest = Body(),
    db: DBManager = Depends(get_db),
):
    category = await db.categories.get_one_or_none(id=post_data.category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # if user_id:
    #     user = await db.users.get_one_or_none(id=user_id)
    #     if not user:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="Author not found"
    #         )

    # Подготавливаем данные для создания

    _post_data = PostAdd(
        category_id=post_data.category_id,
        author_id=user_id,  # ← ID из токена
        title=post_data.title,
        content=post_data.content,
        photo=post_data.photo,
    )

    # _post_data = PostAdd(category_id=category_id, username_id=author_id,**post_data.model_dump())
    post = await db.posts.add(_post_data)
    await db.commit()

    return {"status": "OK", "data": post}


@router.put("/{post_id}", response_model=PostResponse)
async def edit_post(
    post_id: int,
    post_data: PostPatch,
    user_id: UserIdDep,
    db: DBManager = Depends(get_db),
):

    post = await db.posts.get_one_or_none(id=post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != user_id:
        raise HTTPException(status_code=403, detail="You are not the author")

    if post_data.category_id is not None:

        category = await db.categories.get_one_or_none(id=post_data.category_id)

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    updated_post = await db.posts.edit(post_data, id=post_id)

    await db.commit()

    return updated_post


@router.patch("/{post_id}", response_model=Post)
async def partially_edit_post(
    post_id: int,
    post_db: PostPatchRequest,
    user_id: UserIdDep,
    db: DBManager = Depends(get_db),
):
    existing_post = await db.posts.get_one_or_none(id=post_id)
    if not existing_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if existing_post.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the author of this post",
        )
    if post_db.category_id is not None:
        category = await db.categories.get_one_or_none(id=post_db.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {post_db.category_id} not found",
            )
    _post_data = PostPatch(**post_db.model_dump(exclude_unset=True))

    await db.posts.edit(_post_data, exclude_unset=True, id=post_id)

    await db.commit()
    updated_post = await db.posts.get_one_or_none(id=post_id)
    return updated_post


@router.delete("/{post_id}")
async def delete_post(post_id: int, db: DBManager = Depends(get_db)):
    await db.posts.delete(id=post_id)
    await db.commit()
    return {"status": "OK"}
