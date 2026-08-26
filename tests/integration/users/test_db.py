import pytest

from app.core.db_manager import DBManager
from app.core.database import SessionLocal
from app.schemas.users import UserUpdate


@pytest.mark.asyncio
async def test_create_user():
    async with DBManager(session_factory=SessionLocal) as db:
        user = await db.users.create_user(
            name="wepr",
            password_hash="hashed_password",
        )

        await db.commit()

    assert user.id is not None
    assert user.name== "wepr"
    assert user.password_hash == "hashed_password"

@pytest.mark.asyncio
async def test_get_user_by_id(user):

    async with DBManager(session_factory=SessionLocal) as db:

        result = await db.users.get_user_by_id(
            user.id
        )

    assert result is not None
    assert result.id == user.id
    assert result.name == user.name    

@pytest.mark.asyncio
async def test_get_user_by_name(user):

    async with DBManager(session_factory=SessionLocal) as db:

        result = await db.users.get_user_by_name(
            user.name
        )

    assert result is not None
    assert result.id == user.id
    assert result.name == user.name

@pytest.mark.asyncio
async def test_get_user_not_found():
    async with DBManager(session_factory=SessionLocal) as db:
        result = await db.users.get_one_or_none(
            id=999999
        )

    assert result is None    


@pytest.mark.asyncio
async def test_get_all_users():
    async with DBManager(session_factory=SessionLocal) as db:
        user1 = await db.users.create_user(
            name="user1com",
            password_hash="hash1",
        )

        user2 = await db.users.create_user(
            name="user2com",
            password_hash="hash2",
        )

        await db.commit()

        users = await db.users.get_all()

    assert len(users) == 2
    assert users[0].name == "user1com"
    assert users[1].name == "user2com"    

@pytest.mark.asyncio
async def test_update_user(user):

    async with DBManager(session_factory=SessionLocal) as db:

        updated = await db.users.update_user(
            user.id,
            UserUpdate(
                name="UpdatedName"
            ),
        )

        await db.commit()

    assert updated is not None
    assert updated.id == user.id
    assert updated.name == "UpdatedName" 

@pytest.mark.asyncio
async def test_partial_update_user(user):

    old_password_hash = user.password_hash

    async with DBManager(session_factory=SessionLocal) as db:

        updated = await db.users.update_user(
            user.id,
            UserUpdate(
                name="NewName"
            ),
        )

        await db.commit()

    assert updated is not None
    assert updated.name == "NewName"
    assert updated.password_hash == old_password_hash    

# @pytest.mark.asyncio
# async def test_delete_user(user):

#     async with DBManager(session_factory=SessionLocal) as db:

#         result = await db.users.delete_user(user.id)

#         await db.commit()

#     assert result is True    

# @pytest.mark.asyncio
# async def test_delete_user_check(user):

#     async with DBManager(session_factory=SessionLocal) as db:

#         await db.users.delete_user(user.id)
#         await db.commit()

#         result = await db.users.get_user_by_id(user.id)

#     assert result is None    

# @pytest.mark.asyncio
# async def test_delete_user_not_found():

#     async with DBManager(session_factory=SessionLocal) as db:

#         result = await db.users.delete_user(999999)

#     assert result is False    

## авторизация

@pytest.mark.asyncio
async def test_register_user(client):

    response = await client.post(
        "/auth/register",
        json={
            "name": "Nikolay",
            "password": "12345678",
        },
    )

    print(response.status_code)
    print(response.json())

    assert response.status_code in (200, 201)


@pytest.mark.asyncio
async def test_register_duplicate_user(client):
    payload = {
        "name": "duplicate.com",
        "password": "12345678",
    }

    response1 = await client.post(
        "/auth/register",
        json=payload,
    )

    response2 = await client.post(
        "/auth/register",
        json=payload,
    )

    assert response1.status_code in (200, 201)
    assert response2.status_code in (400, 409)   

@pytest.mark.asyncio
async def test_login_jwt(client, user):
    response = await client.post(
        "/auth/login/jwt",
        json={
            "name": user.name,
            "password": "12345678",
        },
    )

    print(response.status_code)
    print(response.json())

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client, user):
    response = await client.post(
        "/auth/login/jwt",
        json={
            "name": user.name,
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401