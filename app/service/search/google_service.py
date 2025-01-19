import subprocess
import serpapi
import os
import re


def download_article(command):
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
        snippet = article.get('snippet')
        publication_info = article.get('publication_info', {})
        summary = publication_info.get('summary')
        authors_name = None

        if link and '10.' in link:
            doi = '/'.join(link[link.find('10.'):].split('/')[:2])

        if title:
            sanitized_title = sanitize_filename(title)           
            base_dir = os.path.abspath("/papers") 
            output_file = os.path.join(base_dir, f"{sanitized_title}.pdf")
            os.makedirs(base_dir, exist_ok=True) 

            if download_article(f'scidownl download --title "{title}" --out "{output_file}"'):
                print(f"Статья успешно скачана по заголовку: {output_file}")
            elif doi and download_article(f'scidownl download --doi "{doi}" --out "{output_file}"'):
                print(f"Статья успешно скачана по DOI: {output_file}")
            else:
                print("Ошибка: статья не найдена ни по заголовку, ни по DOI.")
                continue 

            text = None
            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as f:
                    text = f.read()

            results.append({
                "title": title,
                "doi": doi,
                "link": link,
                "text": text,
                "database": 'Scholar'
            })

    return results
 
