from models.query import Query


class QueryService:
    def __init__(self, session):
        self.session = session

    def add(self, term):
        query = self.session(Query).filter_by(term=term).first()
        if not query:
            new_query = Query(term=term)
            self.session.add(new_query)

    def delete(self, term):
        query = self.session(Query).filter_by(term=term).first()
        if query:
            self.session.delete(query)
        else:
            raise ValueError("Query does not exist")

    def get_articles(self, term):
        query = self.session.query(Query).filter_by(term=term).first()
        if not query:
            raise ValueError("Query does not exist")
        articles = query.articles
        return articles

    def query_list(self):
        query_list = self.session.query(Query).all()
        return query_list
