from sqlalchemy import Integer, String, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship, mapped_column


class Article(Base):

    __tablename__ = 'articles'

    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String, unique=True, nullable=True)
    snippet = mapped_column(String, nullable=True)
    doi = mapped_column(String, unique=True, nullable=True)
    link = mapped_column(String, unique=True, nullable=True)
    summary = mapped_column(String, nullable=True)
    authors = mapped_column(String, nullable=True)
    full_text = mapped_column(String, nullable=True)
    database = mapped_column(String, nullable=False)
    query_term = mapped_column(Integer, ForeignKey('querys.term'))
    query = relationship("Query", back_populates="article")
