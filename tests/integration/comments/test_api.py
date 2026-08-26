import pytest


# ============================================================
# POST /posts/{post_id}/comments/
# ============================================================


@pytest.mark.asyncio
async def test_create_comment(auth_client, user, post):
    response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Отличный пост!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["text"] == "Отличный пост!"
    assert data["post_id"] == post.id
    assert data["author"]["id"] == user.id
    assert data["parent_id"] is None
    assert "id" in data
    assert "created_at" in data


# # ============================================================
# # POST /posts/{post_id}/comments/
# # Неавторизованный пользователь
# # ============================================================


@pytest.mark.asyncio
async def test_create_comment_unauthorized(client, post):
    response = await client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Комментарий",
        },
    )

    assert response.status_code in (401, 403)


# # ============================================================
# # POST /posts/{post_id}/comments/
# # Несуществующий пост
# # ============================================================


@pytest.mark.asyncio
async def test_create_comment_post_not_found(auth_client, user):
    response = await auth_client.post(
        "/posts/999999/comments/",
        json={
            "text": "Комментарий",
        },
    )

    assert response.status_code == 404


# # ============================================================
# # POST /posts/{post_id}/comments/
# # Пустой комментарий
# # ============================================================


@pytest.mark.asyncio
async def test_create_comment_empty_text(auth_client, user, post):
    response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "",
        },
    )

    assert response.status_code == 422


# # # ============================================================
# # # POST /posts/{post_id}/comments/
# # # Вложенный комментарий
# # # ============================================================


@pytest.mark.asyncio
async def test_create_reply(auth_client, user, post):
    parent_response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Родительский комментарий",
        },
    )

    assert parent_response.status_code == 201

    parent = parent_response.json()

    response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Ответ на комментарий",
            "parent_id": parent["id"],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["text"] == "Ответ на комментарий"
    assert data["parent_id"] == parent["id"]
    assert data["post_id"] == post.id


# # # ============================================================
# # # POST /posts/{post_id}/comments/
# # # Несуществующий parent
# # # ============================================================


@pytest.mark.asyncio
async def test_create_reply_parent_not_found(auth_client, user, post):
    response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Ответ",
            "parent_id": 999999,
        },
    )

    assert response.status_code == 404

# # # ============================================================
# # # GET /posts/{post_id}/comments/
# # # ============================================================


@pytest.mark.asyncio
async def test_get_comments(auth_client, user, post):
    await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Комментарий 1",
        },
    )

    await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Комментарий 2",
        },
    )

    response = await auth_client.get(
        f"/posts/{post.id}/comments/"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2

    texts = {comment["text"] for comment in data}

    assert texts == {
        "Комментарий 1",
        "Комментарий 2",
    }

@pytest.mark.asyncio
async def test_get_comments_post_not_found(auth_client):
    response = await auth_client.get(
        "/posts/999999/comments/"
    )

    assert response.status_code == 404

# # # ============================================================
# # # GET /posts/{post_id}/comments/{comment_id}
# # # ============================================================


@pytest.mark.asyncio
async def test_get_comment(auth_client, user, post):
    create_response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Мой комментарий",
        },
    )

    assert create_response.status_code == 201

    comment = create_response.json()

    response = await auth_client.get(
        f"/posts/{post.id}/comments/{comment['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == comment["id"]
    assert data["text"] == "Мой комментарий"
    assert data["post_id"] == post.id

@pytest.mark.asyncio
async def test_get_comment_not_found(auth_client, post):
    response = await auth_client.get(
        f"/posts/{post.id}/comments/999999"
    )

    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_comment_wrong_post(
    auth_client,
    user,
    post,
    post2,
):
    comment_response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Комментарий",
        },
    )

    assert comment_response.status_code == 201

    comment = comment_response.json()

    response = await auth_client.get(
        f"/posts/{post2.id}/comments/{comment['id']}"
    )

    assert response.status_code == 400


# # # ============================================================
# # # PUT /posts/{post_id}/comments/{comment_id}
# # # ============================================================


@pytest.mark.asyncio
async def test_update_comment(auth_client, user, post):
    create_response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Старый текст",
        },
    )

    assert create_response.status_code == 201

    comment = create_response.json()

    response = await auth_client.put(
        f"/posts/{post.id}/comments/{comment['id']}",
        json={
            "text": "Новый текст",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == comment["id"]
    assert data["text"] == "Новый текст"
    assert data["post_id"] == post.id


@pytest.mark.asyncio
async def test_update_comment_not_found(auth_client, user, post):
    response = await auth_client.put(
        f"/posts/{post.id}/comments/999999",
        json={
            "text": "Новый текст",
        },
    )

    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_comment_empty_text(
    auth_client,
    user,
    post,
):
    create_response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Комментарий",
        },
    )

    comment = create_response.json()

    response = await auth_client.put(
        f"/posts/{post.id}/comments/{comment['id']}",
        json={
            "text": "",
        },
    )

    assert response.status_code == 422

# # ============================================================
# # DELETE /posts/{post_id}/comments/{comment_id}
# # ============================================================


@pytest.mark.asyncio
async def test_delete_comment(auth_client, user, post):
    create_response = await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Удаляемый комментарий",
        },
    )

    assert create_response.status_code == 201

    comment = create_response.json()

    response = await auth_client.delete(
        f"/posts/{post.id}/comments/{comment['id']}"
    )

    assert response.status_code == 204

    # Проверяем, что комментария больше нет
    get_response = await auth_client.get(
        f"/posts/{post.id}/comments/{comment['id']}"
    )

    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_delete_comment_not_found(
    auth_client,
    user,
    post,
):
    response = await auth_client.delete(
        f"/posts/{post.id}/comments/999999"
    )

    assert response.status_code == 404

# # ============================================================
# # GET /posts/{post_id}/comments/{comment_id}/replies
# # ============================================================

@pytest.mark.asyncio
async def test_get_comment_replies(
    auth_client,
    post,
    comment,
    reply,
):
    response = await auth_client.get(
        f"/posts/{post.id}/comments/{comment.id}/replies"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == reply.id
    assert data[0]["text"] == "Ответ на комментарий"
    assert data[0]["parent_id"] == comment.id
    assert data[0]["post_id"] == post.id


@pytest.mark.asyncio
async def test_get_replies_comment_not_found(
    auth_client,
    post,
):
    response = await auth_client.get(
        f"/posts/{post.id}/comments/999999/replies"
    )

    assert response.status_code == 404

# # # ============================================================
# # # GET /posts/{post_id}/comments/stats/count
# # # ============================================================


@pytest.mark.asyncio
async def test_comments_count(
    auth_client,
    user,
    post,
):
    await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Комментарий 1",
        },
    )

    await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Комментарий 2",
        },
    )

    await auth_client.post(
        f"/posts/{post.id}/comments/",
        json={
            "text": "Комментарий 3",
        },
    )

    response = await auth_client.get(
        f"/posts/{post.id}/comments/stats/count"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["post_id"] == post.id
    assert data["total_comments"] == 3

@pytest.mark.asyncio
async def test_comments_count_empty(
    auth_client,
    user,
    post,
):
    response = await auth_client.get(
        f"/posts/{post.id}/comments/stats/count"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["post_id"] == post.id
    assert data["total_comments"] == 0

@pytest.mark.asyncio
async def test_comments_count_post_not_found(auth_client):
    response = await auth_client.get(
        "/posts/999999/comments/stats/count"
    )

    assert response.status_code == 404

                                                                