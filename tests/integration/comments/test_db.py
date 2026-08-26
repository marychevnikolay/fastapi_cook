
import pytest

from app.core.db_manager import DBManager
from app.core.database import SessionLocal
from app.schemas.comments import CommentAdd, CommentUpdateRequest


@pytest.mark.asyncio
async def test_add_comment(user, post):
    async with DBManager(session_factory=SessionLocal) as db:

        comment_data = CommentAdd(
            post_id=post.id,
            author_id=user.id,
            text="Отличный пост!",
        )

        comment = await db.comments.add(comment_data)
        await db.commit()

    assert comment.id is not None
    assert comment.text == "Отличный пост!"
    assert comment.post_id == post.id
    assert comment.author_id == user.id
    assert comment.parent_id is None

@pytest.mark.asyncio
async def test_get_comment(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        comment = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Тестовый комментарий",
            )
        )

        await db.commit()

        result = await db.comments.get_one_or_none(
            id=comment.id
        )

    assert result is not None
    assert result.id == comment.id
    assert result.text == "Тестовый комментарий"
    assert result.post_id == post.id
    assert result.author_id == user.id

@pytest.mark.asyncio
async def test_get_comment_not_found():

    async with DBManager(session_factory=SessionLocal) as db:

        comment = await db.comments.get_one_or_none(
            id=999999
        )

    assert comment is None 


@pytest.mark.asyncio
async def test_get_comments_by_post(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        comment1 = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Первый комментарий",
            )
        )

        comment2 = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Второй комментарий",
            )
        )

        await db.commit()

        comments = await db.comments.get_by_post(
            post_id=post.id
        )

    assert len(comments) == 2

    texts = {comment.text for comment in comments}

    assert texts == {
        "Первый комментарий",
        "Второй комментарий",
    }

@pytest.mark.asyncio
async def test_get_replies(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        parent = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Родительский комментарий",
            )
        )

        await db.commit()

        reply1 = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Ответ №1",
                parent_id=parent.id,
            )
        )

        reply2 = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Ответ №2",
                parent_id=parent.id,
            )
        )

        await db.commit()

        replies = await db.comments.get_replies(
            parent.id
        )

    assert len(replies) == 2

    texts = {reply.text for reply in replies}

    assert texts == {
        "Ответ №1",
        "Ответ №2",
    }

    assert all(
        reply.parent_id == parent.id
        for reply in replies
    )  


@pytest.mark.asyncio
async def test_get_by_post_returns_only_root_comments(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        parent = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Родитель",
            )
        )

        await db.commit()

        await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Ответ",
                parent_id=parent.id,
            )
        )

        await db.commit()

        comments = await db.comments.get_by_post(
            post.id
        )

    assert len(comments) == 1
    assert comments[0].text == "Родитель"
    assert comments[0].parent_id is None                 

@pytest.mark.asyncio
async def test_get_all_comments_by_post(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        parent = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Родитель",
            )
        )

        await db.commit()

        await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Ответ",
                parent_id=parent.id,
            )
        )

        await db.commit()

        comments = await db.comments.get_all_by_post(
            post.id
        )

    assert len(comments) == 2

    texts = {comment.text for comment in comments}

    assert texts == {
        "Родитель",
        "Ответ",
    }


@pytest.mark.asyncio
async def test_get_count_by_post(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Комментарий 1",
            )
        )

        await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Комментарий 2",
            )
        )

        await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Комментарий 3",
            )
        )

        await db.commit()

        count = await db.comments.get_count_by_post(
            post.id
        )

    assert count == 3 


@pytest.mark.asyncio
async def test_edit_comment(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        comment = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Старый текст",
            )
        )

        await db.commit()

        updated = await db.comments.edit(
            CommentUpdateRequest(
                text="Новый текст",
            ),
            id=comment.id,
        )

        await db.commit()

    assert updated is not None
    assert updated.text == "Новый текст"           

@pytest.mark.asyncio
async def test_edit_comment_not_found():

    async with DBManager(session_factory=SessionLocal) as db:

        result = await db.comments.edit(
            CommentUpdateRequest(
                text="Новый текст",
            ),
            id=999999,
        )

    assert result is None

@pytest.mark.asyncio
async def test_check_comment_author(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        comment = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Мой комментарий",
            )
        )

        await db.commit()

        result = await db.comments.check_author(
            comment.id,
            user.id,
        )

    assert result is True

@pytest.mark.asyncio
async def test_check_comment_author_wrong_user(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        comment = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Мой комментарий",
            )
        )

        await db.commit()

        result = await db.comments.check_author(
            comment.id,
            999999,
        )

    assert result is False     


@pytest.mark.asyncio
async def test_delete_comment(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        comment = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Удалить меня",
            )
        )

        await db.commit()

        result = await db.comments.delete(
            id=comment.id
        )

        await db.commit()

        deleted = await db.comments.get_one_or_none(
            id=comment.id
        )

    assert result is True
    assert deleted is None

@pytest.mark.asyncio
async def test_delete_comment_with_replies(user, post):

    async with DBManager(session_factory=SessionLocal) as db:

        parent = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Родитель",
            )
        )

        await db.commit()

        reply = await db.comments.add(
            CommentAdd(
                post_id=post.id,
                author_id=user.id,
                text="Ответ",
                parent_id=parent.id,
            )
        )

        await db.commit()

        await db.comments.delete(
            id=parent.id
        )

        await db.commit()

        deleted_parent = await db.comments.get_one_or_none(
            id=parent.id
        )

        deleted_reply = await db.comments.get_one_or_none(
            id=reply.id
        )

    assert deleted_parent is None
    assert deleted_reply is None               