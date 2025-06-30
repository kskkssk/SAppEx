import os
import time
from Bio import Entrez, Medline
from requests_html import HTMLSession
from http.client import IncompleteRead
from service.search.extract_service import *
from requests.exceptions import ConnectionError


def get_pubmed(search_term, method_list, sort="relevance", max_results=None, field=None, mindate=None, maxdate=None):
    Entrez.email = 'kudasheva0.kudasheva@gmail.com'
    term = f"{search_term}[{field}]" if field else search_term
    try:
        search_handle = Entrez.esearch(db="pubmed", term=term, retmax=max_results, sort=sort, datetype='pdat',
                                       mindate=mindate, maxdate=maxdate)
        search_results = Entrez.read(search_handle)
        search_handle.close()
        article_ids = search_results["IdList"]
    except Exception as e:
        print(f"ОШИБКА: {e}")
        return []
    info = []
    if not article_ids:
        print("Статьи не найдены!")
        return info
    fetch_handle = Entrez.efetch(db="pubmed", id=",".join(article_ids), rettype="medline", retmode="text")
    records = Medline.parse(fetch_handle)
    for record in records:
        text = None
        references = None
        keywords = None
        results = None
        introduction = None
        discussion = None
        methods = None
        conclusion = None

        title = record.get("TI", "N/A")
        sanitized_title = sanitize_filename(title)
        pmcid = record.get("PMC")
        session = HTMLSession()
        headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
        base_url = 'https://pmc.ncbi.nlm.nih.gov/articles/'
        if not os.path.exists("pdf_out"):
            os.makedirs("pdf_out")
        base_dir = os.path.abspath(f"pdf_out/{search_term}")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir, exist_ok=True)
        if pmcid:
            try:
                r = session.get(base_url + pmcid + '/', headers=headers, timeout=5)
                link_element = r.html.find('a[aria-label="Download PDF"]', first=True)
                if link_element:
                    pdf_url = link_element.attrs['href']
                    url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" + pdf_url
                    r = session.get(url, stream=True)

                    pdf_path = os.path.join(base_dir, f"{sanitized_title}.pdf")

                    with open(pdf_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=4000):
                            if chunk:
                                f.write(chunk)
                else:
                    print("PDF download link not found.")
            except ConnectionError as e:
                pass
                out = open('conn_error.txt', 'a')
                out.write(pmcid + '\n')
            except IncompleteRead:
                time.sleep(1)
                continue
        if pmcid is not None:
            reader_path = os.path.join(base_dir, f"{sanitized_title}.pdf")
            if os.path.exists(reader_path):
                sections_text = get_sections(reader_path)
                text = extract_text_from_pdf(reader_path)
                if sections_text:
                    introduction = sections_text.get('introduction') or sections_text.get('background')
                    results = sections_text.get('results') or sections_text.get('results and discussion')
                    discussion = sections_text.get('discussion')
                    conclusion = sections_text.get('conclusion') or sections_text.get('conclusions')
                    methods = sections_text.get('methods') or sections_text.get('materials') or sections_text.get(
                        'materials and methods')
                    keywords = sections_text.get('keywords')
                    references = sections_text.get('references')

        abstract = record.get("AB", "N/A")
        if method_list is []:
            method_check = []
        else:
            method_check = check_methods(methods, abstract, method_list)
        info.append({
          "title": title,
          "summary": record.get("SO", "N/A"),
          "doi": record.get("LID", "N/A").replace("[doi]", "").strip(),
          "publication_date": record.get("DP", "N/A"),
          "abstract": abstract,
          "authors": record.get("AU", "N/A"),
          "text": text,
          "database": 'PMC',
          "references": references,
          "keywords": keywords,
          "introduction": introduction,
          "results": results,
          "discussion": discussion,
          "conclusion": conclusion,
          "methods": methods,
          "method_check": method_check,
        })
    return info
