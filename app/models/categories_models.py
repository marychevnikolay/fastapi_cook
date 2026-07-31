from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.posts import PostOrm

from app.core.database import Base


class CategoryOrm(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))

    posts: Mapped[list["PostOrm"]] = relationship(
        "PostOrm",
        back_populates="category",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
