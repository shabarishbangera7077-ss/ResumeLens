from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    skill_match: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    text_similarity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    matched_skills: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    missing_skills: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    suggestions: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    user: Mapped[User] = relationship(back_populates="analyses")
