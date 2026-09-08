from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class MovieCredit(Base):
    __tablename__ = "movie_credits"
    __table_args__ = (UniqueConstraint("movie_id", "person_id", "role", "cast_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False, index=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    cast_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    character_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    movie: Mapped["Movie"] = relationship(back_populates="credits")
    person: Mapped["Person"] = relationship(back_populates="credits")
