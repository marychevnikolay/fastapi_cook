from app.core.security import security


def test_password_hash_and_verify():
    password = "12345678"

    password_hash = security.hash_password(password)

    assert password_hash != password

    assert security.verify_password(
        password,
        password_hash,
    )

    assert not security.verify_password(
        "wrong_password",
        password_hash,
    )

def test_password_hash_is_different_each_time():
    password = "12345678"

    hash1 = security.hash_password(password)
    hash2 = security.hash_password(password)

    assert hash1 != hash2

    assert security.verify_password(password, hash1)
    assert security.verify_password(password, hash2)    

def test_empty_password():
    password = ""

    password_hash = security.hash_password(password)

    assert security.verify_password(
        password,
        password_hash,
    )

    assert not security.verify_password(
        "12345678",
        password_hash,
    )    