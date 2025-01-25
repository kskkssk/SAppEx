import subprocess
import serpapi
from pypdf import PdfReader
import os
import re


def download_article(command, output_file):
    try:
        result = subprocess.run(command, shell=True, check=True)
        return os.path.exists(output_file)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")
        return False


def sanitize_filename(title):
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', title)
    sanitized = sanitized.strip()[:100] 
    return sanitized


def get_scholar(query, page_size, as_ylo, as_yhi, as_rr=0, as_sdt=0):
    api_key = os.getenv("SERP_API")
    if not api_key:
        raise ValueError("API ключ для SERP API не найден. Убедитесь, что переменная окружения SERP_API установлена.")

    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": api_key,
        "num": page_size,
        "as_yhi": as_yhi,  # to
        "as_ylo": as_ylo,  # from
        "ar_rr": as_rr,  # обзорные статьи = 1
        "as_sdt": as_sdt  # статьи=0, патенты=1
    }

    try:
        client = serpapi.Client(api_key=api_key)
        organic_results = client.search(params)['organic_results']
    except Exception as e:
        print(f"Ошибка при запросе к SERP API: {e}")
        return []

    results = []
    for article in organic_results:
        doi = None
        title = article.get('title')
        link = article.get('link')
        publication_info = article.get('publication_info', {})
        summary = publication_info.get('summary')
        
        match = re.search(r'\b\d{4}\b', summary)
        publication_date = match.group() if match else None 
        
        if link and '10.' in link:
            doi = '/'.join(link[link.find('10.'):].split('/')[:2])

        if title:
            sanitized_title = sanitize_filename(title)           
            base_dir = os.path.abspath("/papers") 
            output_file = os.path.join(base_dir, f"{sanitized_title}.pdf")
            os.makedirs(base_dir, exist_ok=True) 

            if download_article(f'scidownl download --title "{title}" --out "{output_file}"', output_file):
                print(f"Статья успешно скачана по заголовку: {output_file}")
            elif doi and download_article(f'scidownl download --doi "{doi}" --out "{output_file}"', output_file):
                print(f"Статья успешно скачана по DOI: {output_file}")
            else:
                print("Ошибка: статья не найдена ни по заголовку, ни по DOI.")
                continue 

            text = None
            if os.path.exists(output_file):
                reader = PdfReader(output_file)
                num_pages = len(reader.pages)
                chunk_size = 4000
                text = ""
                for page_num in range(num_pages):
                    text += reader.pages[page_num].extract_text() + "\n"
                    text = text.replace('\\n', '\n').replace('\xa0', ' ')

            results.append({
                "title": title,
                "doi": doi,
                "text": text,
                "summary": summary,
                "database": "Scholar",
                "publication_date": publication_date
            })

    return results
 
