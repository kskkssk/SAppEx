from fastapi import Depends, FastAPI, Request, Form, HTTPException, File, WebSocket, WebSocketDisconnect, UploadFile
from database import init_db, get_db
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, FileResponse
from service.search.pubmed_service import get_pubmed
from service.search.extract_service import get_methods_dict, authors_count
from service.search.google_service import get_scholar
from service.process.excel import process_excel
from service.process.docx import *
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from service.crud.query_service import QueryService
from service.crud.article_service import ArticleService
from service.crud.sector_service import SectorService
import redis
from typing import List
import os
import pandas as pd
import json
from collections import Counter
import uvicorn
from fastapi.staticfiles import StaticFiles
import socketio
import time
import zipfile
import traceback
import aiofiles
import logging
from logging.handlers import RotatingFileHandler
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=2),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi')
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="/ws/socket.io")
background_task_started = False

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

redis_instance = redis.Redis(host='redis', port=6379, db=0)

SECRET_KEY = os.getenv('SECRET_KEY')
REDIS_URL = os.getenv('REDIS_URL')
REDIS_URL = os.getenv('REDIS_URL')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

app.on_event('startup')


def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    return ArticleService(db)


def get_query_service(db: Session = Depends(get_db)) -> QueryService:
    return QueryService(db)


def get_sector_service(db: Session = Depends(get_db)) -> SectorService:
    return SectorService(db)


active_connections = []  # Хранилище активных WebSocket соединений


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def update_progress(step: str, percent: int):
    for connection in active_connections:
        await connection.send_text(json.dumps({"step": step, "percent": percent}))


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

    method_check = redis_instance.get("method_check")  # список методов

    method_list = []
    if method_check:
        if isinstance(method_check, bytes):
            method_list = json.loads(method_check.decode('utf-8'))
        else:
            method_list = json.loads(method_check)

    articles = query_service.get_articles(query)
    contain_articles = []
    for article in articles:
        if not article.method_check:
            article.method_check = []

        if not isinstance(article.method_check, list):
            article.method_check = [article.method_check]

        if not method_list or any(m in method_list for m in article.method_check):
            contain_articles.append(article)
    articles_dict = []

    for article in contain_articles:
        sectors = sector_service.get_by_article(article.title)
        if sectors:
            article_dict = {
                "title": article.title,
                "doi": article.doi,
                "publication_date": article.publication_date,
                "full": article.full_text,
                "methods_check": article.method_check,
                "authors": article.authors,
                "abstract": sectors.abstract,
                "keywords": sectors.keywords,
                "references": sectors.references,
                "conclusion": sectors.conclusion,
                "introduction": sectors.introduction,
                "results": sectors.results,
                "discussion": sectors.discussion,
                "methods": sectors.methods,
            }
            articles_dict.append(article_dict)
        else:
            article_dict = {
                "title": article.title,
                "doi": article.doi,
                "publication_date": article.publication_date,
                "full": article.full_text,
                "methods_check": article.method_check,
                "authors": article.authors,
                "abstract": None,
                "keywords": None,
                "references": None,
                "introduction": None,
                "results": None,
                "discussion": None,
                "methods": None
            }
            articles_dict.append(article_dict)

    if not articles_dict:
        return templates.TemplateResponse('none.html', {"request": request})

    df = pd.DataFrame(articles_dict)

    ref_counter = Counter()
    auth_counter = Counter()
    if not df.empty:
        df["authors"] = df["authors"].apply(lambda row: re.sub(r'[{}]', '', row))
        for ref in df["references"]:
            if ref:
                ref_authors = authors_count(ref)
                ref_counter.update(ref_authors)
        for authors in df["authors"]:
            if authors:
                authors = re.sub(r'[""]', '', authors).split(",")
                auth_counter.update(dict(Counter(authors)))

    logger.debug(f"Счетчик в референсах: {ref_counter}")
    redis_instance.set('ref_counter', json.dumps(dict(ref_counter)))
    logger.debug(f"Счетчик авторов: {auth_counter}")
    redis_instance.set('auth_counter', json.dumps(dict(auth_counter)))


    length = len(df)
    redis_instance.set('data', json.dumps(df.to_dict()))
    data = {"length": length}

    if length > 0:
        return templates.TemplateResponse('results.html', {"request": request, "data": data})

    return templates.TemplateResponse('none.html', {"request": request})


@app.get('/download')
async def download():
    if "data" not in redis_instance:
        return "Ошибка: Данные не найдены. Пожалуйста, выполните поиск"
    df_dict = json.loads(redis_instance.get('data'))
    df = pd.DataFrame.from_dict(df_dict)

    auth_count = json.loads(redis_instance.get('auth_counter'))
    auth_counter = pd.DataFrame(list(auth_count.items()), columns=['Автор', 'Количество упоминаний']).sort_values(
        by='Количество упоминаний', ascending=False)

    ref_count = json.loads(redis_instance.get('ref_counter'))
    ref_counter = pd.DataFrame(list(ref_count.items()), columns=['Автор', 'Количество упоминаний']).sort_values(
        by='Количество упоминаний', ascending=False)
    query = redis_instance.get("query")
    if query:
        query = query.decode('utf-8')
    if df.empty:
        return None
    else:
        path = f'pdf_out/{query}/'
        file_dir = os.listdir(path)
        zip_name = f"{os.path.join(DOWNLOAD_FOLDER, query)}.zip"
        excel_name = process_excel(query=query, df=df, auth_counter=auth_counter, ref_counter=ref_counter)
        with zipfile.ZipFile(zip_name, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
            if excel_name:
                zf.write(excel_name, arcname=f"{query}.xlsx")
            for file in file_dir:
                add_file = os.path.join(path, file)
                zf.write(add_file, arcname=f"pdf/{file}")
        return FileResponse(zip_name, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            filename=zip_name)


@app.post('/search')
async def search_articles(
    term: str = Form(...),
    max_results: int = Form(...),
    field: str = Form(...),
    mindate: str = Form(...),
    maxdate: str = Form(...),
    as_sdt: float = Form(...),
    as_rr: int = Form(...),
    method: List[str] = Form([]),
    article_service: ArticleService = Depends(get_article_service),
    query_service: QueryService = Depends(get_query_service),
    sector_service: SectorService = Depends(get_sector_service)):

    logger.info(f"Начало обработки запроса. Термин: {term}, Макс. результатов: {max_results}, Методы: {method}")

    term = term.strip()
    redis_instance.set('query', term)
    await sio.emit("progress", {"step": "Начало", "percent": 0})
    if "All" in method:
        method_dict = get_methods_dict()
        method = method_dict.keys()
    redis_instance.set('method_check', json.dumps(list(method)))
    query_service.add(term=term)

    try:

        logger.info("Загрузка данных PubMed...")
        await update_progress("Загрузка данных PubMed...", 25)
        pubmed_results = get_pubmed(search_term=term, method_list=method, max_results=max_results, field=field,
                                    mindate=mindate, maxdate=maxdate)
        for res in pubmed_results:
            logger.debug(f"Обработка статьи PubMed: {res['title']}")
            try:
                article_service.add(term=term, title=res["title"], summary=res["summary"],
                                    authors=res["authors"], doi=res["doi"],
                                    publication_date=res["publication_date"], full_text=res["text"],
                                    database=res["database"], method_check=res["method_check"])
                sector_service.add(title=res["title"], abstract=res["abstract"], keywords=res["keywords"],
                                   introduction=res["introduction"], methods=res["methods"], results=res["results"],
                                   discussion=res["discussion"], conclusion=res["conclusion"], references=res["references"])
            except Exception as e:
                logger.error(f"Ошибка Google Scholar статьи: {traceback.format_exc()}")

        logger.info("Загрузка данных Google Scholar...")
        await update_progress("Загрузка данных Google Scholar...", 50)
        google_results = get_scholar(query=term, max_results=max_results, as_ylo=mindate[:4],
                                     as_yhi=maxdate[:4], as_rr=as_rr, as_sdt=as_sdt, method_list=method)
        for res in google_results:
            logger.debug(f"Обработка статьи Google Scholar: {res['title']}")
            try:
                article_service.add(term=term, title=res["title"], summary=res["summary"],
                                    authors=res["authors"], doi=res["doi"],
                                    publication_date=res["publication_date"], full_text=res["text"],
                                    database=res["database"], method_check=res["method_check"])
                sector_service.add(title=res["title"], abstract=res["abstract"], keywords=res["keywords"],
                                   introduction=res["introduction"], methods=res["methods"], results=res["results"],
                                   discussion=res["discussion"], conclusion=res["conclusion"], references=res["references"])
            except Exception as e:
                logger.error(f"Ошибка Google Scholar статьи: {traceback.format_exc()}")

        time.sleep(2)
        logger.info("Завершение обработки данных")
        await update_progress("Завершение обработки", 75)
        time.sleep(2)
        await update_progress("Готово!", 100)
        logger.info("Запрос успешно обработан")
        return RedirectResponse(url='/results', status_code=303)
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}", exc_info=True)
        await sio.emit("progress", {"step": "Ошибка", "percent": 0, "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/process')
async def process(request: Request):
    return templates.TemplateResponse(request=request, name='process.html')


@app.post('/process/file')
async def process_file(
        file: UploadFile = File(...),
        number: int = Form(...),
        method: List[str] = Form([]),
        section: List[str] = Form([])
):
    try:
        logger.info(f"Starting file processing for {file.filename}")

        if "All" in method:
            method_dict = get_methods_dict()
            method = list(method_dict.keys())

        filename = os.path.splitext(file.filename)[0]  # Без расширения
        filepath = os.path.join(UPLOAD_FOLDER, filename + '.xlsx')

        # Сохраняем файл
        async with aiofiles.open(filepath, 'wb') as buffer:
            await buffer.write(await file.read())

        logger.info(f"File saved to {filepath}, starting processing...")
        word_name = process_word(filename, number, method, section)

        if not os.path.exists(word_name):
            raise HTTPException(status_code=500, detail="Output file was not created")

        return FileResponse(
            word_name,
            filename=f"{filename}.docx",
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def startup():
    init_db()


#app.mount('/search', socket_app)
#app.mount('/', socket_app)

if __name__ == '__main__':
    uvicorn.run(socket_app, host='0.0.0.0', port=8080)
