import os

from app.schemas.posts import PostAdd

os.environ["MODE"] = "TEST"

from dotenv import load_dotenv

load_dotenv(".env-test", override=True)

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from app.core.security import security 

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.core.db_manager import DBManager
from app.schemas.categories import CategoryAdd
from app.schemas.users import UserCreate


@pytest.fixture(autouse=True)
def check_test_mode():
    assert settings.MODE == "TEST"


@pytest_asyncio.fixture(autouse=True)
async def setup_database(check_test_mode):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(setup_database):
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="session", autouse=True)
async def dispose_engine():
    yield
    await engine.dispose()

@pytest_asyncio.fixture
async def user(setup_database):
    async with DBManager(session_factory=SessionLocal) as db:
        user = await db.users.create_user(
            name="testcom",
            password_hash=security.hash_password("12345678"),
        )

        await db.commit()

        return user

@pytest_asyncio.fixture
async def auth_client(client, user):

    response = await client.post(
        "/auth/login/jwt",
        json={
            "name": user.name,
            "password": "12345678",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {token}"

    return client
    
    
@pytest_asyncio.fixture
async def category():
    async with DBManager(session_factory=SessionLocal) as db:
        category = await db.categories.add(
            CategoryAdd(title="Супы")
        )
        await db.commit()

        return category   

@pytest_asyncio.fixture
async def post(user, category):
    async with DBManager(session_factory=SessionLocal) as db:
        post = await db.posts.add(
            PostAdd(
                title="Борщ",
                content="Рецепт борща",
                photo="borsch.jpg",
                category_id=category.id,
                author_id=user.id,
            )
        )

        await db.commit()

        return post  

import pytest_asyncio

from app.core.db_manager import DBManager
from app.core.database import SessionLocal
from app.schemas.comments import CommentAdd


@pytest_asyncio.fixture
async def comment(setup_database, user, post):
    async with DBManager(session_factory=SessionLocal) as db:
        comment = await db.comments.add(
            CommentAdd(
                text="Основной комментарий",
                post_id=post.id,
                author_id=user.id,
            )
        )

        await db.commit()

        return comment      

@pytest_asyncio.fixture
async def reply(setup_database, user, post, comment):
    async with DBManager(session_factory=SessionLocal) as db:
        reply = await db.comments.add(
            CommentAdd(
                text="Ответ на комментарий",
                post_id=post.id,
                author_id=user.id,
                parent_id=comment.id,
            )
        )

        await db.commit()

        return reply
    

@pytest_asyncio.fixture
async def client2():
    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as ac:
        yield ac    


@pytest_asyncio.fixture
async def post2(setup_database, user, category):
    async with DBManager(session_factory=SessionLocal) as db:
        post = await db.posts.add(
            PostAdd(
                title="Второй пост",
                content="Контент второго поста",
                photo="test2.jpg",
                category_id=category.id,
                author_id=user.id,
            )
        )

        await db.commit()

        return post        