from app.models.query import Query


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
