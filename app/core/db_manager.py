from typing import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.repositories.categories_repositories import CategoryRepository
from app.repositories.comments import CommentRepository
from app.repositories.posts import PostsRepository
from app.repositories.users import AuthRepository, UserRepository


class DBManager:
    def __init__(self, session_factory: Callable[[], AsyncSession] = SessionLocal):
        self.session_factory = session_factory
        self.session: AsyncSession | None = None
        self.users: UserRepository | None = None
        self.auth: AuthRepository | None = None

    async def __aenter__(self) -> "DBManager":
        self.session = self.session_factory()

        self.users = UserRepository(self.session)
        self.auth = AuthRepository(self.session)

        self.categories = CategoryRepository(self.session)
        self.posts = PostsRepository(self.session)
        self.comments = CommentRepository(self.session)
        
        return self

    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.session.rollback()
        finally:
            await self.session.close()

    async def commit(self) -> None:
        if self.session:
            await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def close(self):
        await self.session.close()
