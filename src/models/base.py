from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.api.v1.schemas import FileInfo
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

    def as_dict(self) -> FileInfo:
        return FileInfo(
            id=self.id,
            name=self.name,
            created_at=self.created_at,
            path=self.path,
            size=self.size,
        )
