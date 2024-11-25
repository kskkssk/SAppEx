from app.api import app


@app.delete('/delete_article')
def delete_article():
    pass


@app.delete('/delete_query')
def delete_query():
    pass
