from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from app.database import db
from datetime import timedelta
import pandas as pd
import random
import time
import tempfile
import os
import redis

app = Flask(__name__)
redis_instance = redis.Redis(host='localhost', port=6379, db=0)

SECRET_KEY = os.getenv('SECRET_KEY')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
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


class Search:
    def __init__(self, pages: int, query: str, fr, to):
        self.pages = int(pages)
        self.query = query
        self.fr = fr
        self.to = to
        self.driver = self.init_driver()

    @staticmethod
    def init_driver():
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        return driver

    def search(self, start=0):
        base_url = 'https://scholar.google.com/scholar'
        params = f"?start={start}&q={self.query}&hl=ru&as_sdt=0,5&as_ylo={self.fr}&as_yhi={self.to}"
        self.driver.get(base_url + params)
        self.driver.implicitly_wait(10)
        return self.driver.page_source

    @staticmethod
    def parse_content(html):
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        for article in soup.select('.gs_ri'):
            title, href, authors, snippet, doi = None, None, None, None, None

            title_tag = article.select_one('.gs_rt')
            if title_tag:
                title = title_tag.text.strip()
                link_tag = title_tag.find('a')
                if link_tag:
                    href = link_tag.get('href')
                    if '10.' in href:
                        doi = '/'.join(href[href.find('10.'):].split('/')[:2])

            snippet_tag = article.select_one('.gs_rs')
            if snippet_tag:
                snippet = snippet_tag.text.strip()

            authors_tag = article.select_one('.gs_a')
            if authors_tag:
                authors = authors_tag.text.strip()

            articles.append({
                'title': title,
                'href': href,
                'authors': authors,
                'snippet': snippet,
                'doi': doi
            })
        return articles

    def scrape_multiple_pages(self):
        all_articles = []
        for i in range(self.pages):
            start = i * 10
            if i > 2:
                time.sleep(random.uniform(6, 10))
            html_content = self.search(start=start)
            articles = self.parse_content(html_content)
            all_articles.extend(articles)
            time.sleep(random.uniform(5, 7))

        df = pd.DataFrame(all_articles)
        length = len(all_articles)
        return df, length

    def download(self):
        df, _ = self.scrape_multiple_pages()
        df.to_csv(f"{self.query}.csv", index=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results', methods=['POST'])
def results():
    query = request.form['query']
    pages = int(request.form['pages'])
    from_year = request.form['from']
    to_year = request.form['to']

    search = Search(pages=pages, query=query, fr=from_year, to=to_year)
    if search:
        df, length = search.scrape_multiple_pages()
        redis_instance.set('data', df.to_json())
        redis_instance.set('query', query)
        return render_template('results.html', data=df.head().to_html(index=False, classes='dataframe'), length=length)
    else:
        return "Ошибка: Поиск не был инициирован."


@app.route('/download', methods=['GET'])
def download():
    if "data" not in redis_instance:
        return "Ошибка: Данные не найдены. Пожалуйста, выполните поиск"
    df = pd.read_json(redis_instance.get('data'))
    with tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', suffix='.csv') as temp_file:
        df.to_csv(temp_file, index=False)
        temp_file_path = temp_file.name

    try:
        return send_file(temp_file_path, as_attachment=True, download_name=f'{redis_instance.get("query")}.csv')
    finally:
        os.remove(temp_file_path)


if __name__ == '__main__':
    '''
    with app.app_context():
        db.create_all()
    '''
    app.run(debug=True)
