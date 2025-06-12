from sqlalchemy import Integer, ForeignKey, Text, JSON
from database import Base
from sqlalchemy.orm import relationship, mapped_column


class Section(Base):
    __tablename__ = 'sections'

    id = mapped_column(Integer, primary_key=True)
    abstract = mapped_column(Text, nullable=True)
    keywords = mapped_column(JSON, nullable=True)
    introduction = mapped_column(Text, nullable=True)
    methods = mapped_column(Text, nullable=True)
    results = mapped_column(Text, nullable=True)
    discussion = mapped_column(Text, nullable=True)
    conclusion = mapped_column(Text, nullable=True)
    references = mapped_column(Text, nullable=True)
    article_id = mapped_column(Integer, ForeignKey('articles.id'))
    article = relationship("Article", back_populates="sec_data")
