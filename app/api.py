from flask import Flask, render_template, request, send_file
from selenium import webdriver
from serpapi import GoogleSearch
from Bio import Entrez, Medline
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup
from database import db
from datetime import timedelta
import pandas as pd
import random
import time
import tempfile
import os
import json
import redis

app = Flask(__name__)
redis_instance = redis.Redis(host='redis', port=6379, db=0)

SECRET_KEY = os.getenv('SECRET_KEY')
REDIS_URL = os.getenv('REDIS_URL')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

app.secret_key = SECRET_KEY
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'flask_session:'
app.config['SESSION_REDIS'] = redis.from_url(REDIS_URL)
'''
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
'''
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)


def process_scholar(results):
    for article in results:
        doi = None
        title = None
        link = None
        snippet = None
        summary = None
        authors_name = None
        title = article['title']
        link = article['link']
        if link:
            if '10.' in link:
                doi = '/'.join(link[link.find('10.'):].split('/')[:2])
        snippet = article['snippet']
        publication_info = article['publication_info']
        if publication_info:
            summary = publication_info['summary']
            if 'authors' in publication_info:
                authors = publication_info['authors']
                if authors:
                    authors_info = authors[0]
                    if authors_info:
                        authors_name = authors_info['name']
    source = 'google scholar'


def get_scholar(query, api_key, start, page_size, as_ylo, as_yhi):
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "start": start,
        "num": page_size,
        "as_yhi": as_yhi,  # to
        "as_ylo": as_ylo  # from
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    organic_results = results["organic_results"]
    return organic_results


def get_pubmed(query, max_results=10, from_year=None, to_year=None):
    Entrez.email = "kudasheva0.kudasheva@gmail.com"
    results = []
    if from_year and to_year:
        search_term = f'{query} AND ({from_year} : {to_year}) AND (("{from_year}/01/01"[PDat] : "{to_year}/12/31"[PDat]))'
    elif from_year:
        search_term = f'{query} AND (("{from_year}/01/01"[PDat] : "3000/12/31"[PDat]))'
    elif to_year:
        search_term = f'{query} AND (("0001/01/01"[PDat] : "{to_year}/12/31"[PDat]))'
    else:
        search_term = query

    search_handle = Entrez.esearch(db="pubmed", term=search_term, retmax=max_results)
    search_results = Entrez.read(search_handle)
    search_handle.close()

    article_ids = search_results["IdList"]

    if not article_ids:
        print("Статьи не найдены!")
        return results

    fetch_handle = Entrez.efetch(db="pubmed", id=",".join(article_ids), rettype="medline", retmode="text")

    records = Medline.parse(fetch_handle)

    for record in records:
        pmc_id = record.get('PMC', None)
        full_text = None
        if pmc_id:
            try:
                handle = Entrez.efetch("pubmed", id=pmc_id, retmode="xml")
                full_text = handle.read()
                handle.close()
            except Exception as e:
                full_text = f"Текст не доступен {e}"
        results.append({
            "title": record.get("TI", "N/A"),
            "authors": record.get("AU", "N/A"),
            "source": record.get("SO", "N/A"),
            "doi": record.get("LID", "N/A").replace("[doi]", "").strip(),
            "abstract": record.get("AB", "N/A"),
            "publication_date": record.get("DP", "N/A"),
            "text": full_text
        })

    return results


def process_pubmed(articles):
    for article in articles:
        print(f"  Название: {article['title']}")
        print(f"  Авторы: {article['authors']}")
        print(f"  Источник: {article['source']}")
        print(f"  DOI: {article['doi']}")
        print(f"  Аннотация: {article['abstract']}")
        print(f"  Дата публикации: {article['publication_date']}")
        print('\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results', methods=['POST'])
def results():
    query = request.form['query']
    pages = int(request.form['pages'])
    from_year = request.form['from']
    to_year = request.form['to']

    goo_articles = get_scholar(
        query=query,
        api_key=os.getenv("API_KEY"),
        start=0,
        page_size=pages,
        as_ylo=from_year,
        as_yhi=to_year
    )
    pub_articles = get_pubmed(
        query=query,
        max_results=pages,
        from_year=from_year,
        to_year=to_year
    )

        #redis_instance.set('data', json.dumps(df_dict))
        #redis_instance.set('query', query)
        #return render_template('results.html', data=df.head().to_html(index=False, classes='dataframe'), length=length)
   # else:
       # return "Ошибка: Поиск не был инициирован."


@app.route('/download', methods=['GET'])
def download():
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
        return send_file(temp_file_path, as_attachment=True, download_name=f'{query}.csv')
    finally:
        os.remove(temp_file_path)


if __name__ == '__main__':
    '''
    with app.app_context():
        db.create_all()
    '''
    app.run(host="0.0.0.0", port=5000, debug=True)
