
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
