from app.database import db


class Article(db.Model):

    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(1000), nullable=True)
    snippet = db.Column(db.Text, nullable=True)
    doi = db.Column(db.String(100), nullable=True)
    authors = db.Column(db.String(500), nullable=True)


class Experiment(db.Model):

    __tablename__ = 'experiments'

    pass

