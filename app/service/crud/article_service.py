from models.article import Article
from models.query import Query
from service.crud.query_service import QueryService


class ArticleService:
    def __init__(self, session):
        self.session = session
        self.query_session = QueryService(session)

    def add(self, term, title, doi, summary, authors, publication_date, full_text, database, method_check):
        query = self.session.query(Query).filter_by(term=term).first()
        if not query:
            raise ValueError("Query with such term does not exist")
        existing_article = self.session.query(Article).filter(
            Article.title.ilike(f"%{title}%"),  # Нечувствительное к регистру частичное сопоставление
            Article.doi == doi if doi else True
        ).first()
        if not existing_article:
            new_article = Article(
                title=title,
                doi=doi,
                summary=summary,
                authors=authors,
                publication_date=publication_date,
                full_text=full_text,
                database=database,
                query=query,
                method_check=method_check
            )
            self.session.add(new_article)
            self.session.commit()

    def get_by_title(self, title: str):
        article = self.session.query(Article).filter_by(title=title).first()
        return article

    def get_by_authors(self, authors: str):
        articles = self.session.query(Article).filter_by(authors=authors).first()
        return articles

    def get_by_doi(self, doi: str):
        article = self.session.query(Article).filter_by(doi=doi).first()
        return article
