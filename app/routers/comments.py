from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from app.routers.dependencies import DBManager, UserIdDep, PaginationDep, get_db
from app.schemas.comments import (
    CommentAddRequest,
    CommentAdd,
    CommentUpdateRequest,
    CommentResponse,
)
from app.models.posts import PostOrm
from app.models.users import UserOrm
from app.models.comments import CommentsOrm

router = APIRouter(prefix="/posts/{post_id}/comments", tags=["Комментарии"])


# ============================================
# ПОЛУЧЕНИЕ КОММЕНТАРИЕВ К ПОСТУ
# ============================================


@router.get("/", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: int, pagination: PaginationDep, db: DBManager = Depends(get_db)
):
    """
    Получить все комментарии к посту (с пагинацией)
    """
    # Проверяем существование поста
    post = await db.posts.get_one_or_none(id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # Получаем комментарии
    per_page = pagination.per_page or 20
    comments = await db.comments.get_by_post(
        post_id=post_id, limit=per_page, offset=per_page * (pagination.page - 1)
    )

    return comments


# ============================================
# СОЗДАНИЕ КОММЕНТАРИЯ
# ============================================


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    comment_data: CommentAddRequest,
    user_id: UserIdDep,
    db: DBManager = Depends(get_db),
):
    # 1. Проверяем существование поста
    post = await db.posts.get_one_or_none(id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found",  # ← Исправил f-строку
        )

    # 2. Проверяем родительский комментарий (только если parent_id передан)
    parent_comment = None
    if comment_data.parent_id is not None and comment_data.parent_id > 0:
        parent_comment = await db.comments.get_one_or_none(id=comment_data.parent_id)

        # ✅ Проверка внутри блока if
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent comment with id {comment_data.parent_id} not found",
            )

        # ✅ Проверка принадлежности к посту тоже внутри блока
        if parent_comment.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent comment {comment_data.parent_id} does not belong to post {post_id}",
            )

    # 3. Создаем комментарий
    _comment_data = CommentAdd(
        post_id=post_id,
        author_id=user_id,
        text=comment_data.text,
        parent_id=comment_data.parent_id,
    )

    comment = await db.comments.add(_comment_data)
    await db.commit()

    # ✅ Получаем комментарий с загруженными связями
    full_comment = await db.comments.get_one_or_none(id=comment.id)

    if not full_comment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created comment",
        )

    return full_comment


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(post_id: int, comment_id: int, db: DBManager = Depends(get_db)):

    ##Получить комментарий по ID
    comment = await db.comments.get_one_or_none(id=comment_id)

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    ##Проверяем, что комментарий относится к этому посту
    if comment.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this post",
        )

    return comment


@router.put("/{comment_id}", response_model=CommentResponse)
async def edit_comment(
    post_id: int,
    comment_id: int,
    comment_data: CommentUpdateRequest,
    user_id: UserIdDep,
    db: DBManager = Depends(get_db),
):
    ##Обновить комментарий (только для автора)
    ##Проверяем существование комментария
    comment = await db.comments.get_one_or_none(id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    ##Проверяем, что комментарий относится к этому посту
    if comment.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this post",
        )

    # Проверяем, что пользователь - автор комментария
    if comment.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the author of this comment",
        )

    # Обновляем комментарий
    updated = await db.comments.edit(comment_data, id=comment_id)
    await db.commit()

    # Получаем обновленный комментарий с автором
    full_comment = await db.comments.get_one_or_none(id=comment_id)
    return full_comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    post_id: int, comment_id: int, user_id: UserIdDep, db: DBManager = Depends(get_db)
):

    ##Удалить комментарий

    # Права:Автор комментария может удалить свой комментарий
    # Администратор может удалить любой комментарий
    # Проверяем существование комментария
    comment = await db.comments.get_one_or_none(id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    # Проверяем, что комментарий относится к этому посту
    if comment.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this post",
        )

    # Проверяем права на удаление
    user = await db.users.get_one_or_none(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if comment.author_id != user_id and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this comment",
        )

    # Удаляем комментарий (каскадно удалятся все ответы)
    await db.comments.delete(id=comment_id)
    await db.commit()

    return None


##ПОЛУЧЕНИЕ ОТВЕТОВ НА КОММЕНТАРИЙ
@router.get("/{comment_id}/replies", response_model=List[CommentResponse])
async def get_comment_replies(
    post_id: int, comment_id: int, db: DBManager = Depends(get_db)
):
    comment = await db.comments.get_one_or_none(id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if comment.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this post",
        )

        # Получаем ответы
    replies = await db.comments.get_replies(comment_id)
    return replies


@router.get("/stats/count")
async def get_comments_stats(post_id: int, db: DBManager = Depends(get_db)):

    # Получить статистику комментариев к посту
    # Проверяем существование поста
    post = await db.posts.get_one_or_none(id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    total = await db.comments.get_count_by_post(post_id)

    return {"post_id": post_id, "total_comments": total}
