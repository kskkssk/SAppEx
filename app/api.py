from fastapi import Depends, FastAPI, Request, Response, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_db
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
import redis
import os
import pandas as pd
import json
import tempfile
import uvicorn
from fastapi.responses import FileResponse
from service.search.pubmed_service import get_pubmed
from service.search.google_service import get_scholar
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from service.crud.query_service import QueryService
from service.crud.article_service import ArticleService

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

redis_instance = redis.Redis(host='redis', port=6379, db=0)

SECRET_KEY = os.getenv('SECRET_KEY')
REDIS_URL = os.getenv('REDIS_URL')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')


app.on_event('startup')

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def get_guery_service(db: Session = Depends(get_db)):
    return QueryService(db)


def get_article_service(db: Session = Depends(get_db)):
    return ArticleService(db)


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )


@app.get('/results')
async def results(request: Request):
    query = redis_instance.get("query")
    length_google = redis_instance.get("length_google")
    length_pubmed = redis_instance.get("length_pubmed")
    query_service = get_guery_service()
    articles = query_service.get_articles(query)
    # чтобы сделать датафрейм из SqlAlchemy , надо сделать словарь
    articles_dict = [{
        "title": article.title,
        "snippet": article.snippet,
        "doi": article.doi,
        "link": article.link,
        "summary": article.summary,
        "source": article.source,
        "authors": article.authors,
        "abstract": article.abstract,
        "publication_date": article.publication_date,
        "full_text": article.full_text,
        "database": article.database
    } for article in articles]
    df = pd.DataFrame(articles_dict)
    df_dict = df.to_dict()
    redis_instance.set('data', json.dumps(df_dict))
    data = {"length_google": length_google,
            "length_pubmed": length_pubmed,
            "df": df.head().to_html(index=False, classes='dataframe')
            }
    return templates.TemplateResponse(
        'results.html', {"request": request, "data": data}
    )


@app.get('/download')
async def download():
    if "data" not in redis_instance:
        return "Ошибка: Данные не найдены. Пожалуйста, выполните поиск"
    df_dict = json.loads(redis_instance.get('data'))
    df = pd.DataFrame.from_dict(df_dict, orient='index')
    query = redis_instance.get("query")
    if query:
        query = query.decode('utf-8')
    with tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', suffix='.csv') as temp_file:
        df.to_csv(temp_file, index=False)
        temp_file_path = temp_file.name
    try:
        return FileResponse(temp_file_path, filename=f'{query}.csv')
    finally:
        os.remove(temp_file_path)


@app.get('/query_list')
async def query_list(request: Request):
    query_service = get_guery_service()
    querys = query_service.query_list()
    if not querys:
        return None
    data = {"querys": querys}
    return templates.TemplateResponse(
        'query_list.html', {"request": request, "data": data}
    )


@app.post('/search')
async def search_articles(term: str = Form(...),
                          sort: str = Form(...),
                          max_results: int = Form(...),
                          field: str = Form(...),
                          n: int = Form(...),
                          mindate: str = Form(...),
                          maxdate: str = Form(...),
                          as_sdt: float = Form(...),
                          as_rr: int = Form(...)):
    redis_instance.set('query', term)

    pubmed_results = get_pubmed(term, sort=sort, max_results=max_results, field=field, n=n, mindate=mindate,
                                maxdate=maxdate)
    article_service = get_article_service()
    for res in pubmed_results:
        article_service.add(
            term=term, title=res["title"], authors=res["authors"], source=res["source"],
            doi=res["doi"], abstract=res["abstract"], publication_date=res["publication_date"],
            full_text=res["text"], database=res["database"]
        )
    redis_instance.set('length_pubmed', len(pubmed_results))

    google_results = get_scholar(query=term, page_size=max_results, as_ylo=mindate, as_yhi=maxdate, as_rr=as_rr,
                                 as_sdt=as_sdt)
    for res in google_results:
        article_service.add(
            term=term, title=res["title"], snippet=res["snippet"], doi=res["doi"],
            link=res["link"], summary=res["summary"], authors=res["authors"], database=res["database"]
        )
    redis_instance.set('length_google', len(google_results))

    return RedirectResponse(url='/results', status_code=303)


@app.delete('/query')
def delete_query(query: str):
    try:
        query_service = get_guery_service()
        query_service.delete(query)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"message": "Query deleted successfully"}


def startup():
    init_db()


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8083)
