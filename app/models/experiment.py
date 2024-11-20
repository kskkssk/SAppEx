from app.database import db


class Experiment(db.Model):

    __tablename__ = 'experiment'

    method = db.Column(db.String(1000), nullable=True)
    doi = db.Column(db.String(100), nullable=True)
    circs = db.Column(db.String(), nullable=True)
