from fastapi import APIRouter, HTTPException, status, Response, Depends, Request
from app.core.config import settings
from app.routers.dependencies import (
    DBDep,
    get_current_user_from_bearer,
    get_current_user_from_session,
)
from app.schemas.users import (
    UserCreate,
    UserRead,
    LoginRequest,
    RefreshRequest,
    TokenPair,
    LoginRequest,
    SessionLoginResponse,
)
from app.services.auth import UserService, AuthServiceJWT, AuthServiceSession
from app.core.exceptions import (
    AppError,
    InvalidCredentialsError,
    RefreshTokenExpiredError,
    RefreshTokenNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.models.users import UserOrm
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import oauth2_scheme
from app.core.limiter import limiter
router = APIRouter(prefix="/auth", tags=["Пользователи"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
)
@limiter.limit("5/minute")
async def register(data: UserCreate, db: DBDep, request: Request) -> UserRead:
    service = UserService(db)
    try:
        return await service.register(data.name, data.password)
    except UserAlreadyExistsError as err:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="User already exists"
        ) from err
    except AppError as err:
        detail = str(err) or "Bad request"
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=detail) from err


def _set_token_cookies(
    response: Response, access_token: str, refresh_token: str
) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=access_token,
        httponly=False,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path="/",
    )
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=False,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path="/",
    )


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    # Проверка пользователя
    if form_data.username != "admin":
        raise Exception("Неверный логин")

    access_token = "jwt_token"

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/login/jwt", summary="Вход через JWT (access + refresh)")
async def login_with_jwt(
    data: LoginRequest, response: Response, db: DBDep
) -> TokenPair:
    jwt_service = AuthServiceJWT(db)
    try:
        access_token, refresh_token = await jwt_service.login(data.name, data.password)
    except InvalidCredentialsError as err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(err)) from err
    except AppError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    _set_token_cookies(response, access_token, refresh_token)
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/token/refresh", summary="Обновление access/refresh токенов")
async def refresh_tokens(
    data: RefreshRequest, response: Response, db: DBDep
) -> TokenPair:
    jwt_service = AuthServiceJWT(db)
    try:
        pair = await jwt_service.refresh(data.refresh_token)
    except RefreshTokenExpiredError as err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(err)) from err
    except RefreshTokenNotFoundError as err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(err)) from err
    except UserNotFoundError as err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(err)) from err
    except AppError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    _set_token_cookies(response, pair.access_token, pair.refresh_token)
    return pair


@router.get("/me/jwt", summary="Профиль по JWT (access)")
async def me_jwt(user: UserOrm = Depends(get_current_user_from_bearer)) -> UserRead:
    return user


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=False,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.SESSION_TTL_MINUTES * 60,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        domain=settings.SESSION_COOKIE_DOMAIN,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        path="/",
    )


@router.post(
    "/login/session",
    summary="Вход через session",
)
async def login_with_session(
    data: LoginRequest, response: Response, db: DBDep
) -> SessionLoginResponse:
    session_service = AuthServiceSession(db)
    try:
        user, raw_token = await session_service.login(data.name, data.password)
    except InvalidCredentialsError as err:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(err)) from err
    except AppError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    _set_session_cookie(response, raw_token)
    return SessionLoginResponse(user=user)


@router.post("/logout/session", summary="Выход из session")
async def logout_session(request: Request, response: Response, db: DBDep) -> dict:
    session_service = AuthServiceSession(db)
    raw_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    try:
        await session_service.logout(raw_token)
    except AppError as err:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    _clear_session_cookie(response)
    return {"detail": "Logged out"}


@router.get("/me/session", summary="Профиль по session")
async def me_session(
    user: UserOrm = Depends(get_current_user_from_session),
) -> UserRead:
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    return token


@router.get("/profile")
async def profile(
    token: str = Depends(get_current_user),
):
    return {"token": token}
