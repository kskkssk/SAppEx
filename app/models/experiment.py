from sqlalchemy import Integer, String, ForeignKey, Text, JSON
from database import Base
from sqlalchemy.orm import relationship, mapped_column


class Experiment(Base):
    __tablename__ = 'experiments'

    id = mapped_column(Integer, primary_key=True)
    objects = mapped_column(String, nullable=True)
    methods = mapped_column(JSON, nullable=True)
    parameters = mapped_column(JSON, nullable=True)
    results = mapped_column(Text, nullable=True)
    notes = mapped_column(Text, nullable=True)
    article_id = mapped_column(Integer, ForeignKey('articles.id'))
    article = relationship("Article", back_populates="exp_data")
