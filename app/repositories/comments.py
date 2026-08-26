from typing import Optional, List
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.comments import CommentsOrm
from app.schemas.comments import CommentAdd, CommentUpdateRequest, CommentResponse


class CommentRepository(BaseRepository):
    """Репозиторий для работы с комментариями"""

    model = CommentsOrm
    schema = CommentResponse

    async def add(self, data: CommentAdd) -> CommentsOrm:
        """Создать новый комментарий"""
        instance = self.model(
            text=data.text,
            post_id=data.post_id,
            author_id=data.author_id,
            parent_id=data.parent_id,
        )
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_one_or_none(self, **filters) -> Optional[CommentsOrm]:
        """Получить один комментарий с автором"""
        query = (
            select(self.model)
            .filter_by(**filters)
            .options(
                selectinload(self.model.author),
                selectinload(self.model.replies).selectinload(CommentsOrm.author),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_post(
        self,
        post_id: int,
        limit: int = 50,
        offset: int = 0,
        include_replies: bool = True,
    ) -> List[CommentsOrm]:
        """
        Получить комментарии к посту (только корневые, без parent_id)
        """
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.post_id == post_id,
                    self.model.parent_id.is_(None),  # Только корневые комментарии
                )
            )
            .options(
                selectinload(self.model.author),
                selectinload(self.model.replies).selectinload(
                    CommentsOrm.author
                ),  # Загружаем авторов ответов
            )
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_replies(self, parent_id: int) -> List[CommentsOrm]:
        query = (
            select(self.model)
            .where(self.model.parent_id == parent_id)
            .options(
                selectinload(self.model.author),
                selectinload(self.model.replies).selectinload(
                    CommentsOrm.author
                ),
            )
            .order_by(self.model.created_at)
        )

        result = await self.session.execute(query)

        return result.scalars().all()
    # async def get_replies(self, parent_id: int) -> List[CommentsOrm]:
    #     """Получить ответы на комментарий"""
    #     query = (
    #         select(self.model)
    #         .where(self.model.parent_id == parent_id)
    #         .options(selectinload(self.model.author))
    #         .order_by(self.model.created_at)
    #     )

    #     result = await self.session.execute(query)
    #     return result.scalars().all()

    async def get_all_by_post(
        self, post_id: int, limit: int = 100, offset: int = 0
    ) -> List[CommentsOrm]:
        """Получить все комментарии к посту (включая ответы)"""
        query = (
            select(self.model)
            .where(self.model.post_id == post_id)
            .options(selectinload(self.model.author))
            .order_by(desc(self.model.created_at))
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_count_by_post(self, post_id: int) -> int:
        """Получить количество комментариев к посту"""
        query = select(self.model).where(self.model.post_id == post_id)
        result = await self.session.execute(query)
        return len(result.scalars().all())

    async def edit(
        self, data: CommentUpdateRequest, **filters
    ) -> Optional[CommentsOrm]:
        """Обновить комментарий"""
        instance = await self.get_one_or_none(**filters)
        if instance:
            instance.text = data.text
            await self.session.flush()
        return instance

    async def delete(self, **filters) -> bool:
        """Удалить комментарий"""
        instance = await self.get_one_or_none(**filters)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False

    async def check_author(self, comment_id: int, user_id: int) -> bool:
        """Проверить, является ли пользователь автором комментария"""
        comment = await self.get_one_or_none(id=comment_id)
        if not comment:
            return False
        return comment.author_id == user_id
