from models.section import Section
from models.article import Article

class SectorService:
    def __init__(self, session):
        self.session = session

    def add(self, title, abstract, keywords, introduction, references,
            methods=None, results=None, discussion=None, conclusion=None):
        article = self.session.query(Article).filter_by(title=title).first()
        if not article:
            raise ValueError("Article with such title does not exist")
        existing_sections = self.session.query(Section).filter_by(article=article).all()
        if existing_sections:
            print(f"Warning: Article {title} already has sections: {existing_sections}")
        else:
            section = Section(
                            abstract=abstract,
                            keywords=keywords,
                            introduction=introduction,
                            methods=methods,
                            results=results,
                            discussion=discussion,
                            conclusion=conclusion,
                            references=references,
                            article=article)
            self.session.add(section)
            self.session.commit()

    def delete(self):
        pass

    def get_by_article(self, title: str):
        article = self.session.query(Article).filter_by(title=title).first()
        if not article:
            raise ValueError("Article does not exist")
        return article.sec_data
