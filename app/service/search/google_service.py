import serpapi
import os


def get_scholar(query, page_size, as_ylo, as_yhi, as_rr=0, as_sdt=0.5):
    api_key = os.getenv("API_KEY")
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "num": page_size,
        "as_yhi": as_yhi,  # to
        "as_ylo": as_ylo,  # from
        "ar_rr": as_rr,  # обзорные статьи = 1
        "as_sdt": as_sdt  # статьи и патенты=0.5, статьи=0, патенты=1
    }
    client = serpapi.Client(api_key=api_key)
    organic_results = client.search(params)['organic_results']
    results = []
    for article in organic_results:
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
        results.append({
            "title": title,
            "snippet": snippet,
            "doi": doi,
            "link": link,
            "summary": summary,
            "authors": authors_name,
            "database": 'Scholar'
        })
    return results
