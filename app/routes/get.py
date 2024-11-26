from app.api import app, templates, redis_instance
from app.database import get_db
import os
import pandas as pd
import json
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi import Request, Depends
from app.service.crud.query_service import QueryService
from fastapi.responses import FileResponse
import tempfile


def get_guery_service(db: Session = Depends(get_db)):
    return QueryService(db)


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
    articles = query_service.get_by_query(query)
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
