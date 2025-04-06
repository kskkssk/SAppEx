from sqlalchemy import Integer, String, ForeignKey, Date, JSON, Text
from database import Base
from sqlalchemy.orm import relationship, mapped_column


class Article(Base):
    __tablename__ = 'articles'

    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String, unique=True, nullable=True)
    doi = mapped_column(String, nullable=True)
    summary = mapped_column(String, nullable=True)
    authors = mapped_column(String, nullable=True)
    publication_date = mapped_column(String, nullable=True)
    full_text = mapped_column(Text, nullable=True)
    database = mapped_column(String, nullable=False)
    method_check = mapped_column(JSON, nullable=True)
    query_id = mapped_column(Integer, ForeignKey('querys.id'))
    query = relationship("Query", back_populates="articles")
    sec_data = relationship("Section", back_populates="article", cascade="all, delete-orphan", uselist=False)


