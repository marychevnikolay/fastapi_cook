from typing import List, Optional
from sqlalchemy import delete, insert, select, and_, or_, desc, func, update
from sqlalchemy.orm import selectinload
from app.repositories.base import BaseRepository
from app.models.posts import PostOrm
from app.schemas.posts import Post, PostPatch, PostResponse


class PostsRepository(BaseRepository):
    model = PostOrm
    schema = Post

    async def get_all(
        self, limit: int = 10, offset: int = 0, search: Optional[str] = None
    ):
        stmt = select(PostOrm)

        if search:
            stmt = stmt.where(self.model.title.ilike(f"%{search}%"))

        stmt = (
            stmt.options(
                selectinload(PostOrm.comments),
                selectinload(PostOrm.author),
                selectinload(PostOrm.category),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.scalars(stmt)

        return result.all()

    async def add(self, data: Post) -> PostOrm:
        """
        Создать новый пост

        Args:
            data: Схема с данными для создания поста
        """
        # ✅ Правильно: используем model_dump() для получения словаря
        # и удаляем None значения, если они не нужны
        values = data.model_dump(exclude_unset=True)

        # ✅ Убираем id, если он есть (он должен генерироваться автоматически)
        values.pop("id", None)

        # Создаем запрос на вставку
        stmt = insert(self.model).values(**values).returning(self.model)

        result = await self.session.execute(stmt)
        await self.session.flush()

        # Получаем созданный пост
        post = result.scalar_one()
        return post

    async def get_one_or_none(self, **filters) -> Optional[PostOrm]:
        """Получить один пост по фильтрам"""
        query = select(self.model).filter_by(**filters)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_filtered(
        self,
        category_id: Optional[int] = None,
        author_id: Optional[int] = None,
        is_published: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        order_by: str = "-created_at",
    ) -> List[PostOrm]:
        """Получить посты с фильтрацией"""
        query = select(self.model)

        filters = []
        if category_id is not None:
            filters.append(
                self.model.category_id == category_id
            )  ## необходимо добавить проверку на существование категории
        if author_id is not None:
            filters.append(self.model.author_id == author_id)
        if is_published is not None:
            filters.append(self.model.is_published == is_published)
        if search:
            filters.append(self.model.title.ilike(f"%{search}%"))

        if filters:
            query = query.where(and_(*filters))

        if order_by:
            if order_by.startswith("-"):
                query = query.order_by(desc(getattr(self.model, order_by[1:])))
            else:
                query = query.order_by(getattr(self.model, order_by))

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def increment_watched(self, post_id: int) -> None:
        """Увеличить счетчик просмотров"""
        post = await self.get_one_or_none(id=post_id)
        if post:
            post.watched += 1
            await self.session.flush()

    async def edit(
        self,
        data: PostPatch,
        **filters,
    ):

        values = data.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        values.pop("id", None)

        stmt = (
            update(self.model)
            .filter_by(**filters)
            .values(**values)
            .returning(self.model)
        )

        result = await self.session.execute(stmt)

        await self.session.flush()

        return result.scalar_one()

    async def delete(self, **filters) -> bool:
        """Удалить пост"""
        existing = await self.get_one_or_none(**filters)
        if not existing:
            return False

        stmt = delete(self.model).filter_by(**filters)
        await self.session.execute(stmt)
        await self.session.flush()
        return True
