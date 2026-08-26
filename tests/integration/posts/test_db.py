import pytest
from app.core.db_manager import DBManager
from app.core.database import SessionLocal
from app.schemas.posts import PostAdd, PostPatch 


@pytest.mark.asyncio
async def test_add_post(user, category):
    post_data = PostAdd(
        category_id=category.id,
        author_id=user.id,
        title="Борщ",
        content="12345",
        photo="123.jpg",
    )

    async with DBManager(session_factory=SessionLocal) as db:
        post = await db.posts.add(post_data)
        await db.commit()

    assert post.id is not None
    assert post.author_id == user.id
    assert post.category_id == category.id
    assert post.title == "Борщ"
    assert post.content == "12345"
    assert post.photo == "123.jpg"


@pytest.mark.asyncio
async def test_get_one_post(post):
    async with DBManager(session_factory=SessionLocal) as db:
        result = await db.posts.get_one_or_none(id=post.id)

    assert result is not None
    assert result.id == post.id
    assert result.title == "Борщ"
    assert result.content == "Рецепт борща"
    assert result.category_id == post.category_id
    assert result.author_id == post.author_id      

@pytest.mark.asyncio
async def test_get_one_post_not_found():
    async with DBManager(session_factory=SessionLocal) as db:
        result = await db.posts.get_one_or_none(id=999999)

    assert result is None

@pytest.mark.asyncio
async def test_get_all_posts(user, category):
    async with DBManager(session_factory=SessionLocal) as db:
        post1 = await db.posts.add(
            PostAdd(
                title="Борщ",
                content="Рецепт борща",
                photo="borsch.jpg",
                category_id=category.id,
                author_id=user.id,
            )
        )

        post2 = await db.posts.add(
            PostAdd(
                title="Суп",
                content="Рецепт супа",
                photo="soup.jpg",
                category_id=category.id,
                author_id=user.id,
            )
        )

        await db.commit()

        posts = await db.posts.get_all()

    assert len(posts) == 2
    assert posts[0].title == "Борщ"
    assert posts[1].title == "Суп"

@pytest.mark.asyncio
async def test_update_post(post):
    async with DBManager(session_factory=SessionLocal) as db:
        updated_post = await db.posts.edit(
            PostPatch(
                title="Обновленный борщ",
                content="Новый рецепт",
                photo="new_borsch.jpg",
            ),
            id=post.id,
        )

        await db.commit()

    assert updated_post is not None
    assert updated_post.id == post.id
    assert updated_post.title == "Обновленный борщ"
    assert updated_post.content == "Новый рецепт"
    assert updated_post.photo == "new_borsch.jpg"

@pytest.mark.asyncio
async def test_partial_update_post(post):
    old_content = post.content
    old_photo = post.photo

    async with DBManager(session_factory=SessionLocal) as db:
        updated_post = await db.posts.edit(
            PostPatch(
                title="Новый борщ"
            ),
            exclude_unset=True,
            id=post.id,
        )

        await db.commit()

    assert updated_post is not None
    assert updated_post.id == post.id
    assert updated_post.title == "Новый борщ"
    assert updated_post.content == old_content
    assert updated_post.photo == old_photo         


@pytest.mark.asyncio
async def test_delete_post(post):
    async with DBManager(session_factory=SessionLocal) as db:
        result = await db.posts.delete(id=post.id)
        await db.commit()

        deleted_post = await db.posts.get_one_or_none(
            id=post.id
        )

    assert result is True
    assert deleted_post is None

@pytest.mark.asyncio
async def test_delete_post_not_found():
    async with DBManager(session_factory=SessionLocal) as db:
        result = await db.posts.delete(id=999999)

    assert result is False               