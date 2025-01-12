from models.experiment import Experiment
from models.article import Article

class ExperimentService:
    def __init__(self, session):
        self.session = session

    def add(self, title, objects, methods, parameters, results, notes):
        article = self.session.query(Article).filter_by(title=title).first()
        if not article:
            raise ValueError("Article with such title does not exist")
        experiment = Experiment(objects=objects,
                                methods=methods,
                                parameters=parameters,
                                results=results,
                                notes=notes,
                                article=article)
        self.session.add(experiment)
        self.session.commit()

    def delete(self):
        pass

    def get_by_article(self, title: str):
        article = self.session.query(Article).filter_by(title=title).first()
        if not article:
            raise ValueError("Article does not exist")
        return article.exp_data
