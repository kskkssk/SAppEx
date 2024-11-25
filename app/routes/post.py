from app.api import app
from app.service.crud.article_service import ArticleService
from app.service.crud.query_service import QueryService
from app.service.search.pubmed_service import get_pubmed
from fastapi import Form


@app.post('/add_pubmed')
async def add_pubmed(term: str = Form(...), sort: str = Form(...), max_results: str = Form(...),
                     field: str = Form(...), n: int = Form(...), mindate: str = Form(...), maxdate: str = Form(...)):
    results = get_pubmed(term, sort=sort, max_results=max_results, field=field, n=n, mindate=mindate, maxdate=maxdate)
    for res in results:
        title = res["title"],
        authors = res["authors"],
        source = res["source"],
        doi = res["doi"],
        abstract = res["abstract"],
        publication_date = res["publication_date"],
        full_text = res["text"],
        database = res["database"]
    new_article = ArticleService.add(term=term, title=title, snippet=snippet, doi=doi, link=link,
                                     summary=summary, authors=authors, full_text=full_text, database=database)


@app.route('/results')
async def results():
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