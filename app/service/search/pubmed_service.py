from requests.exceptions import ConnectionError
from http.client import IncompleteRead
from requests_html import HTMLSession
from Bio import Entrez, Medline
from pypdf import PdfReader
from openai import OpenAI
import pandas as pd
import time
import json
import os

'''
def send_request(chunk):
    #api_key = os.getenv("OPENAI_API_KEY")
    api_key = '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'

    client = OpenAI(
        api_key=api_key,
    )
    first_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages = [
            {
                "role": "system",
                "content": "Ты — помощник, который анализирует тексты и отвечает 'Да' или 'Нет' на вопрос, есть ли в тексте условия для экспериментов."
            },
            {
                "role": "user",
                "content":
                    "Проанализируй текст и ответь 'Да', если в тексте есть условия для экспериментов (например, описание объектов, методов, параметров или результатов исследований). "
                    "Если таких условий нет, ответь 'Нет'. "
                    "Ответь только 'Да' или 'Нет' без дополнительных пояснений.\n"
                    f"Текст для анализа:\n{chunk}"
            }
        ]
    )
    first_response = first_response.choices[0].message.content
    if first_response.lower().strip() == 'да':
        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Вы - полезный помощник, который анализирует тексты и структурирует данные в формате, совместимом с JSON."
                },
                {
                    "role": "user",
                    "content":
                        "Проанализируй текст и создай список словарей. Каждый словарь соответствует одному объекту исследования. "
                        "Формат каждого словаря должен быть следующим:\n"
                        "{\n"
                        "  \"objects\": \"название объекта\",\n"
                        "  \"methods\": [\"метод_1\", \"метод_2\", ...],\n"
                        "  \"parameters\": [\"параметр_1\", \"параметр_2\", ...],\n"
                        "  \"results\": \"описание результатов\",\n"
                        "  \"notes\": \"дополнительные примечания\"\n"
                        "}\n"
                        "Если какой-то элемент отсутствует в тексте, оставь его пустым (например, пустой список или пустую строку).\n"
                        "Убедись, что все строки заключены в двойные кавычки (\"), чтобы данные были совместимы с форматом JSON.\n"
                        "Предоставь только список словарей, без дополнительных комментариев или пояснений.\n"
                        f"Текст для анализа:\n{chunk}"
                }
            ]
        )
        content = second_response.choices[0].message.content
        print("Response content:", content)  # Логируем содержимое ответа
        print(type(content))
        if content:  
            try:
                result = json.loads(content.replace("'", '"').replace('\'', '\"').replace('\\', '\\\\').strip("'<>() "))
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
                print("Response content:", content)
                return None 
            return result
        else:
            return None
'''

def get_pubmed(search_term, sort="relevance", max_results=None, field=None, mindate=None, maxdate=None):
    Entrez.email = 'kudasheva0.kudasheva@gmail.com'
    term = f"{search_term}[{field}]" if field else search_term

    search_handle = Entrez.esearch(db="pubmed", term=term, retmax=max_results, sort=sort, datetype='pdat',
                                   mindate=mindate, maxdate=maxdate)
    search_results = Entrez.read(search_handle)
    search_handle.close()
    results = []
    responses = []
    article_ids = search_results["IdList"]

    if not article_ids:
        print("Статьи не найдены!")
        return results

    fetch_handle = Entrez.efetch(db="pubmed", id=",".join(article_ids), rettype="medline", retmode="text")
    records = Medline.parse(fetch_handle)
    for record in records:
        pmcid = record.get("PMC")
        session = HTMLSession()
        headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
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
            #try:
            reader = PdfReader(f"{pmcid}.pdf")
            num_pages = len(reader.pages)
            chunk_size = 4000
            text = ""
            for page_num in range(num_pages):
                text += reader.pages[page_num].extract_text() + "\n"
                text = text.replace('\xa0', ' ')
                text = re.sub(r"\\n|\n|\r\n", " ", text)
                '''
                chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
                for idx, chunk in enumerate(chunks):
                    response = send_request(chunk)
                    if response:
                        responses.extend(response)
                '''
            #except Exception as e:
            #    print(f"Ошибка при чтении PDF: {e}")
            #    continue
            results.append({
              "title": record.get("TI", "N/A"),
              "summary": record.get("SO", "N/A"),
              "doi": record.get("LID", "N/A").replace("[doi]", "").strip(),
              "abstract": record.get("AB", "N/A"),
              "publication_date": record.get("DP", "N/A"),
              "text": text,
              "database": 'PMC',
              #"experimental_data": ''
            })
    return results
