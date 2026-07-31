from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.users import UserOrm
    from app.models.categories_models import CategoryOrm
    from app.models.comments import CommentsOrm


class PostOrm(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    # updated_at: Mapped[datetime] = mapped_column(
    #     DateTime,
    #     server_default=func.now(),
    #     onupdate=func.now(),
    #     nullable=False
    # )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
        onupdate=func.now(),
    )

    photo: Mapped[str] = mapped_column(String(1000), nullable=True)
    watched: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Используем строки для связей
    author: Mapped["UserOrm"] = relationship(
        "UserOrm", back_populates="posts", lazy="selectin"
    )

    category: Mapped["CategoryOrm"] = relationship(
        "CategoryOrm", back_populates="posts", lazy="selectin"
    )
    comments: Mapped[list["CommentsOrm"]] = relationship(
        "CommentsOrm",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
