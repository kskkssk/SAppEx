from requests.exceptions import ConnectionError
from http.client import IncompleteRead
from requests_html import HTMLSession
from Bio import Entrez, Medline
from pypdf import PdfReader
import time


def get_pubmed(search_term, sort="relevance", max_results=None, field=None, n=None, mindate=None, maxdate=None):
    Entrez.email = "kudasheva0.kudasheva@gmail.com"
    term = f"{search_term}[{field}]" if field else search_term

    search_handle = Entrez.esearch(db="pubmed", term=term, retmax=max_results, reldate=n, sort=sort, datetype='pdat',
                                   mindate=mindate, maxdate=maxdate)
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
        pmcid = record.get("PMC")
        session = HTMLSession()
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                 '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'}
        base_url = 'https://pmc.ncbi.nlm.nih.gov/articles/'
        text = None
        if pmcid:
            try:
                r = session.get(base_url + pmcid + '/', headers=headers, timeout=5)
                link_element = r.html.find('a[aria-label="Download PDF"]', first=True)
                if link_element:
                    pdf_url = link_element.attrs['href']
                    url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/" + pdf_url
                    r = session.get(url, stream=True)
                    with open(pmcid + '.pdf', 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
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
            try:
                reader = PdfReader(f"{pmcid}.pdf")
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                    text = text.replace('\n', '').replace('\xa0', ' ')
            except Exception as e:
                print(f"Ошибка при чтении PDF: {e}")
                continue

            results.append({
              "title": record.get("TI", "N/A"),
              "authors": record.get("AU", "N/A"),
              "source": record.get("SO", "N/A"),
              "doi": record.get("LID", "N/A").replace("[doi]", "").strip(),
              "abstract": record.get("AB", "N/A"),
              "publication_date": record.get("DP", "N/A"),
              "text": text,
              "database": 'PMC'
            })
    return results
