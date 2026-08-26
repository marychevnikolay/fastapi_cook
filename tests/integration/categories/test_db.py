import pytest

from app.core.db_manager import DBManager
from app.core.database import SessionLocal
from app.schemas.categories import CategoryAdd, CategoryPatch


@pytest.mark.asyncio
async def test_add_category():
    category_data = CategoryAdd(title="Супы")

    async with DBManager(session_factory=SessionLocal) as db:
        category = await db.categories.add(category_data)
        await db.commit()

    assert category.id is not None
    assert category.title == "Супы"


@pytest.mark.asyncio
async def test_get_category():
    async with DBManager(session_factory=SessionLocal) as db:
        created = await db.categories.add(
            CategoryAdd(title="Десерты")
        )

        await db.commit()

        category = await db.categories.get_one_or_none(
            id=created.id
        )

        assert category is not None
        assert category.id == created.id
        assert category.title == "Десерты"

@pytest.mark.asyncio
async def test_get_all_categories():
    async with DBManager(session_factory=SessionLocal) as db:
        await db.categories.add(CategoryAdd(title="Напитки"))
        await db.categories.add(CategoryAdd(title="Супы"))
        await db.commit()

        categories = await db.categories.get_all()

    assert len(categories) == 2
    assert categories[0].title == "Напитки"
    assert categories[1].title == "Супы"


@pytest.mark.asyncio
async def test_search_category():
    async with DBManager(session_factory=SessionLocal) as db:
        await db.categories.add(CategoryAdd(title="Холодные напитки"))
        await db.categories.add(CategoryAdd(title="Горячие блюда"))
        await db.commit()

        categories = await db.categories.get_all(
            search="напитки"
        )

    assert len(categories) == 1
    assert categories[0].title == "Холодные напитки"


@pytest.mark.asyncio
async def test_edit_category():
    async with DBManager(session_factory=SessionLocal) as db:
        category = await db.categories.add(
            CategoryAdd(title="Напитки")
        )
        await db.commit()

        updated = await db.categories.edit(
            CategoryPatch(title="Алкогольные напитки"),
            id=category.id,
        )

        await db.commit()

    assert updated is not None
    assert updated.id == category.id
    assert updated.title == "Алкогольные напитки"


@pytest.mark.asyncio
async def test_delete_category():
    async with DBManager(session_factory=SessionLocal) as db:
        category = await db.categories.add(
            CategoryAdd(title="Удалить")
        )
        await db.commit()

        result = await db.categories.delete(id=category.id)
        await db.commit()

        deleted = await db.categories.get_one_or_none(id=category.id)

    assert result is True
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_nonexistent_category():
    async with DBManager(session_factory=SessionLocal) as db:
        result = await db.categories.delete(id=999999)

    assert result is False


@pytest.mark.asyncio
async def test_get_count():
    async with DBManager(session_factory=SessionLocal) as db:
        await db.categories.add(CategoryAdd(title="Категория 1"))
        await db.categories.add(CategoryAdd(title="Категория 2"))
        await db.categories.add(CategoryAdd(title="Категория 3"))
        await db.commit()

        count = await db.categories.get_count()

    assert count == 3