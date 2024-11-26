from app.api import app, redis_instance
from app.service.crud.article_service import ArticleService
from app.service.search.pubmed_service import get_pubmed
from app.service.search.google_service import get_scholar
from fastapi import Form, Depends
from app.database import get_db
from sqlalchemy.orm import Session


def get_article_service(db: Session = Depends(get_db)):
    return ArticleService(db)


@app.post('/pubmed')
async def add_pubmed(term: str = Form(...), sort: str = Form(...), max_results: str = Form(...),
                     field: str = Form(...), n: int = Form(...), mindate: str = Form(...), maxdate: str = Form(...)):
    redis_instance.set('query', term)
    redis_instance.set('length_pubmed', n)
    results = get_pubmed(term, sort=sort, max_results=max_results, field=field, n=n, mindate=mindate, maxdate=maxdate)
    article_service = get_article_service()
    for res in results:
        title = res["title"]
        authors = res["authors"]
        source = res["source"]
        doi = res["doi"]
        abstract = res["abstract"]
        publication_date = res["publication_date"]
        text = res["text"]
        database = res["database"]
        article_service.add(term=term, title=title, authors=authors, source=source, doi=doi,
                            abstract=abstract, publication_date=publication_date, full_text=text, database=database)
    redis_instance.set('length_pubmed', len(results))
    return None


@app.post('/google')
async def add_google(term: str = Form(...), as_sdt: float = Form(...), max_results: str = Form(...),
                     as_rr: int = Form(...), mindate: str = Form(...), maxdate: str = Form(...)):
    redis_instance.set('length_google', max_results)
    results = get_scholar(query=term, page_size=max_results, as_ylo=mindate, as_yhi=maxdate, as_rr=as_rr, as_sdt=as_sdt)
    article_service = get_article_service()
    for res in results:
        title = res["title"]
        snippet = res["snippet"]
        doi = res["doi"]
        link = res["link"]
        summary = res["summary"]
        authors = res["authors"]
        database = res["database"]
        article_service.add(term=term, title=title, snippet=snippet, doi=doi, link=link,
                            summary=summary, authors=authors, database=database)
    redis_instance.set('length_google', len(results))
    return None
