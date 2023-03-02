from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UUID
from sqlalchemy.orm import relationship

from src.db.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True, index=True)
    username = Column(
        String(length=256), nullable=False, unique=True, index=True
    )
    password = Column(String(length=256), nullable=False)


class File(Base):
    __tablename__ = 'files'

    id = Column(UUID, primary_key=True, index=True)
    name = Column(String(length=256), nullable=False)
    created_at = Column(DateTime, nullable=False)
    path = Column(String(length=256), nullable=False, unique=True, index=True)
    size = Column(Integer, nullable=False)
    user_id = Column(UUID,
                     ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False)
    relationship(User, backref='files')
