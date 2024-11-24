from app.models.article import Article
from app.models.query import Query


class ArticleService:
    def __init__(self, session):
        self.session = session

    def add(self, term: str, title: str, snippet: str, doi: str, link: str, summary: str, authors: str, full_text: str,
            database: str):
        query = self.session.query(Query).filter_by(term=term).first()
        if not query:
            raise ValueError("Query with such term does not exist")
        article = self.session.query(Article).filter_by(title=title, query_term=term).first()
        if not article:
            new_article = Article(
                title=title,
                snippet=snippet,
                doi=doi,
                link=link,
                summary=summary,
                authors=authors,
                full_text=full_text,
                database=database,
                query=query
            )
            self.session.add(new_article)

    def delete(self, query: str):
        articles = self.session.query(Article).filter_by(query=query).all()
        self.session.delete(articles)

    def get_by_title(self, title: str):
        article = self.session.query(Article).filter_by(title=title).first()
        return article

    def get_by_authors(self, authors: str):
        article = self.session.query(Article).filter_by(authors=authors).first()
        return article

    def get_by_doi(self, doi: str):
        article = self.session.query(Article).filter_by(doi=doi).first()
        return article
