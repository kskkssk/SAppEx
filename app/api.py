from flask import Flask, render_template, request, send_file
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
