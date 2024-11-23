from Bio import Entrez, Medline


def custom_term(query,
                from_year='0001',
                from_month='01',
                from_day='01',
                to_day='31',
                to_month='12',
                to_year='3000',
                ):
    Entrez.email = "kudasheva0.kudasheva@gmail.com"
    search_term = f'{query} AND ({from_year} : {to_year}) AND (("{from_year}/{from_month}/{from_day}"[PDat] : "{to_year}/{to_month}/{to_day}"[PDat]))'
    return search_term


def get_pubmed(search_term, max_results):
    search_handle = Entrez.esearch(db="pubmed", term=search_term, retmax=max_results)
    search_results = Entrez.read(search_handle)
    search_handle.close()
    results = []
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


def extract_free():
    pass


def extract_limited():
    pass


def process_pubmed(articles):
    for article in articles:
        print(f"  Название: {article['title']}")
        print(f"  Авторы: {article['authors']}")
        print(f"  Источник: {article['source']}")
        print(f"  DOI: {article['doi']}")
        print(f"  Аннотация: {article['abstract']}")
        print(f"  Дата публикации: {article['publication_date']}")
        print('\n')