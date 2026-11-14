from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, Integer, ForeignKey, Enum, BIGINT
from backend.core.database import Base

class User(Base):

    __tablename__ = "users"

    id: Mapped[BIGINT] = mapped_column()