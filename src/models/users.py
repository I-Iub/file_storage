from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        UUID)
from sqlalchemy.orm import relationship

from src.db.database import Base


class User(Base):
    __tablename__ = 'users'

    uuid = Column(UUID, primary_key=True, index=True)
    username = Column(
        String(length=256), nullable=False, unique=True, index=True
    )
    password = Column(String(length=256), nullable=False)
