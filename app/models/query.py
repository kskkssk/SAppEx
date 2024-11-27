from sqlalchemy import Integer, String, JSON
from database import Base
from sqlalchemy.orm import relationship, mapped_column


class Query(Base):

    __tablename__ = 'querys'

    id = mapped_column(Integer, primary_key=True)
    term = mapped_column(String, nullable=False)
    articles = relationship("Article", back_populates="query", cascade="all, delete-orphan")
