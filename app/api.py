from fastapi import Depends, FastAPI, Request, Response, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_db
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from service.search.pubmed_service import get_pubmed
from service.search.google_service import get_scholar
from service.process.excel import process_excel
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from service.crud.query_service import QueryService
from service.crud.article_service import ArticleService
from service.crud.sector_service import SectorService
import redis
import os
from io import BytesIO
import pandas as pd
import json
import uvicorn

app = FastAPI()

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


def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    return ArticleService(db)


def get_query_service(db: Session = Depends(get_db)) -> QueryService:
    return QueryService(db)


def get_sector_service(db: Session = Depends(get_db)) -> SectorService:
    return SectorService(db)


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )


@app.get('/results')
async def results(request: Request,
                  query_service: QueryService = Depends(get_query_service),
                  sector_service: SectorService = Depends(get_sector_service)):
    query = redis_instance.get("query")
    if query:
        query = query.decode('utf-8')
    print(f"QUERY {query}")
    length_google = redis_instance.get("length_google")
    length_pubmed = redis_instance.get("length_pubmed")
    articles = query_service.get_articles(query)
    print(f"ARTICLES {articles}")

    articles_dict = []
    for article in articles:
        print(f"SECTORS for {article.title}")
        sectors = sector_service.get_by_article(article.title)
        print(f"SECTORS {sectors}")
        if sectors:
            sector = sectors[0]
            article_dict = {
                "title": article.title,
                "doi": article.doi,
                "publication_date": article.publication_date,
                "database": article.database,
                "abstract": sector.abstract,
                "keywords": sector.keywords,
                "references": sector.references
            }
            articles_dict.append(article_dict)
        else:
            article_dict = {
                "title": article.title,
                "doi": article.doi,
                "publication_date": article.publication_date,
                "database": article.database,
                "abstract": None,
                "keywords": None,
                "references": None
            }
            articles_dict.append(article_dict)

    df = pd.DataFrame(articles_dict)
    redis_instance.set('data', json.dumps(df.to_dict()))

    data = {
        "length_google": length_google,
        "length_pubmed": length_pubmed,
        #"df": df.head().to_html(index=False, classes='dataframe')
    }

    return templates.TemplateResponse(
        'results.html', {"request": request, "data": data}
    )


@app.get('/download')
async def download():
    if "data" not in redis_instance:
        return "Ошибка: Данные не найдены. Пожалуйста, выполните поиск"
    df_dict = json.loads(redis_instance.get('data'))
    df = pd.DataFrame.from_dict(df_dict)
    query = redis_instance.get("query")
    if query:
        query = query.decode('utf-8')
    else:
        query = "data"
    filename = f"{query}.xlsx"
    process_excel(query=query, df=df)
    return FileResponse(filename, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        filename=filename)
'''
#байтовая последоватекльность. обработаем df 
file_content = df.to_csv(index=False, sep=';').encode('utf-8')
file_like = BytesIO(file_content)
file_like.seek(0)
headers = {'Content-Disposition': f'attachment; filename="{query}.csv"'}
return StreamingResponse(file_like, media_type='application/octet-stream', headers=headers)
'''


@app.get('/query_list')
async def query_list(request: Request, query_service: QueryService = Depends(get_query_service)):
    querys = query_service.query_list()
    if not querys:
        return None
    data = {"querys": querys}
    return templates.TemplateResponse(
        'query_list.html', {"request": request, "data": data}
    )


@app.post('/search')
async def search_articles(term: str = Form(None),
                          max_results: int = Form(None),
                          field: str = Form(None),
                          mindate: str = Form(None),
                          maxdate: str = Form(None),
                          as_sdt: float = Form(None),
                          as_rr: int = Form(None),
                          article_service: ArticleService = Depends(get_article_service),
                          sector_service: SectorService=Depends(get_sector_service)):
    term = term.strip()
    redis_instance.set('query', term)

    pubmed_results = get_pubmed(term, max_results=max_results, field=field, mindate=mindate,
                                maxdate=maxdate)
    for res in pubmed_results:
        article_service.add(
            term=term, title=res["title"], summary=res["summary"], doi=res["doi"],
            publication_date=res["publication_date"], full_text=res["text"], database=res["database"])
        sector_service.add(
            title=res["title"], abstract=res["abstract"], keywords=res["keywords"], introduction=None,
            methods=None, results=None, discussion=None, conclusion=None, references=res["references"])

    redis_instance.set('length_pubmed', len(pubmed_results))
    
    google_results = get_scholar(query=term, page_size=max_results, as_ylo=mindate[:4], as_yhi=maxdate[:4], as_rr=as_rr,
                                 as_sdt=as_sdt)

    for res in google_results:
        article_service.add(
            term=term, title=res["title"], summary=res["summary"],  doi=res["doi"], 
            publication_date=res["publication_date"], full_text=res["text"], database=res["database"])
        sector_service.add(
            title=res["title"], abstract=res["abstract"], keywords=res["keywords"], introduction=None,
            methods=None, results=None, discussion=None, conclusion=None, references=res["references"])

    redis_instance.set('length_google', len(google_results))

    return RedirectResponse(url='/results', status_code=303)


@app.delete('/query')
def delete_query(query: str, query_service: QueryService = Depends(get_query_service)):
    try:
        query_service.delete(query)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"message": "Query deleted successfully"}


def startup():
    init_db()


if __name__ == '__main__':
    uvicorn.run(app, host='147.45.135.3', port=8080)
