from sqlalchemy import delete, insert, select, func, update
from typing import Optional, List

from app.repositories.base import BaseRepository
from app.models.categories_models import CategoryOrm
from app.schemas.categories import Category, CategoryAdd, CategoryPatch


class CategoryRepository(BaseRepository):
    model = CategoryOrm
    schema = Category

    async def get_all(
        self, limit: int = 10, offset: int = 0, search: Optional[str] = None
    ) -> List[Category]:
        """
        Получить все категории с пагинацией и поиском
        """
        # ✅ Используем self.model, а не Category
        query = select(self.model)

        # Поиск по названию (если передан)
        if search:
            query = query.where(
                func.lower(self.model.name).contains(search.strip().lower())
            )

        # Пагинация
        query = query.limit(limit).offset(offset)

        # Выполняем запрос
        result = await self.session.execute(query)
        categories = result.scalars().all()

        # Конвертируем SQLAlchemy модели в Pydantic схемы
        return [
            self.schema.model_validate(category, from_attributes=True)
            for category in categories
        ]

    async def get_one_or_none(self, **filter_by) -> Optional[Category]:
        """
        Получить одну категорию по фильтрам
        """
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        category = result.scalars().one_or_none()

        if category is None:
            return None

        return self.schema.model_validate(category, from_attributes=True)

    async def get_by_name(self, name: str) -> Optional[Category]:
        """
        Получить категорию по названию
        """
        return await self.get_one_or_none(name=name)

    async def add(self, data: CategoryAdd) -> Category:
        """
        Создать новую категорию
        """
        # ✅ Используем self.model
        add_data_stmt = (
            insert(self.model).values(**data.model_dump()).returning(self.model)
        )
        result = await self.session.execute(add_data_stmt)
        category = result.scalars().one()

        return self.schema.model_validate(category, from_attributes=True)

    async def edit(
        self, data: CategoryPatch, exclude_unset: bool = False, **filter_by
    ) -> Optional[Category]:
        """
        Обновить категорию
        """
        # Проверяем, существует ли категория
        existing = await self.get_one_or_none(**filter_by)
        if not existing:
            return None

        # Обновляем
        update_stmt = (
            update(self.model)
            .filter_by(**filter_by)
            .values(**data.model_dump(exclude_unset=exclude_unset))
            .returning(self.model)
        )
        result = await self.session.execute(update_stmt)
        category = result.scalars().one()

        return self.schema.model_validate(category, from_attributes=True)

    async def delete(self, **filter_by) -> bool:
        """
        Удалить категорию
        """
        # Проверяем, существует ли категория
        existing = await self.get_one_or_none(**filter_by)
        if not existing:
            return False

        # Удаляем
        delete_stmt = delete(self.model).filter_by(**filter_by)
        await self.session.execute(delete_stmt)
        return True

    async def get_count(self, search: Optional[str] = None) -> int:
        """
        Получить количество категорий
        """
        query = select(func.count()).select_from(self.model)

        if search:
            query = query.where(
                func.lower(self.model.name).contains(search.strip().lower())
            )

        result = await self.session.execute(query)
        return result.scalar()
