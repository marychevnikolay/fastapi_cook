from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.users import UserOrm
    from app.models.categories_models import PostOrm


class CommentsOrm(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped["UserOrm"] = relationship(
        "UserOrm", back_populates="comments", lazy="selectin"
    )
    post: Mapped["PostOrm"] = relationship(
        "PostOrm", back_populates="comments", lazy="selectin"
    )
    # Родительский комментарий (для вложенности)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Дочерние комментарии
    replies: Mapped[list["CommentsOrm"]] = relationship(
        "CommentsOrm",
        back_populates="parent",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    parent: Mapped["CommentsOrm"] = relationship(
        "CommentsOrm", back_populates="replies", remote_side=[id], lazy="selectin"
    )
