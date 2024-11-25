from app.api import app
import os
import pandas as pd
import json


@app.route('/')
async def index():
    return render_template('index.html')


@app.route('/download')
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
        return send_file(temp_file_path, as_attachment=True, download_name=f'{query}.csv')
    finally:
        os.remove(temp_file_path)
