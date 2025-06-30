import os
import re
import serpapi
import subprocess
from service.search.extract_service import *
from requests.exceptions import RequestException


def download_article(command, output_file):
    try:
        subprocess.run(command, shell=True, check=True, timeout=120)

        if os.path.exists(output_file):
            return True
        else:
            print(f"Ошибка: файл не был создан: {output_file}")
            return False
    except subprocess.TimeoutExpired:
        print(f"Тайм-аут при выполнении команды: {command}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")
        return False
    except RequestException as e:
        print(f"Сетевая ошибка: {e}")
        return False
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return False


def get_scholar(query, method_list, max_results, as_ylo, as_yhi, as_rr=0, as_sdt=0):
    api_key = os.getenv("SERP_API")
    if not api_key:
        raise ValueError("API ключ для SERP API не найден. Убедитесь, что переменная окружения SERP_API установлена.")

    info = []
    page_size = 20
    num_queries = (max_results + page_size - 1) // page_size  # округляем вверх

    for i in range(num_queries):
        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": api_key,
            "start": i * page_size,
            "as_yhi": as_yhi,  # to
            "as_ylo": as_ylo,  # from
            "as_rr": as_rr,  # обзорные статьи = 1
            "as_sdt": as_sdt  # статьи=0, патенты=1
        }

        try:
            client = serpapi.Client(api_key=api_key)
            search_results = client.search(params)
            organic_results = search_results.get('organic_results', [])
        except Exception as e:
            print(f"Ошибка при запросе к SERP API: {e}")
            continue

        if not organic_results:
            print(f"Нет результатов для {query} на странице {i + 1}")
            continue

        for article in organic_results:
            title = article.get('title')
            link = article.get('link')

            publication_info = article.get('publication_info', {})
            summary = publication_info.get('summary')

            pattern = re.compile(r'([A-Z]+(?:\s?[A-Z]*))\s([A-Z][a-z]+)')
            authors = []
            matches = pattern.findall(summary)
            for match in matches:
                author = f"{match[0]} {match[1]}"  # Объединяем фамилию и инициалы
                authors.append(author)

            match = re.search(r'\b\d{4}\b', summary)
            publication_date = match.group() if match else None

            doi = None
            if link and '10.' in link:
                doi = '/'.join(link[link.find('10.'):].split('/')[:2])

            text, abstract, keywords, introduction, results, discussion, conclusion, methods, references, ref_count = (None,) * 10

            if title:
                sanitized_title = sanitize_filename(title)
                if not os.path.exists("pdf_out"):
                    os.makedirs("pdf_out")
                base_dir = os.path.abspath(f"pdf_out/{query}")
                if not os.path.exists(base_dir):
                    os.makedirs(base_dir, exist_ok=True)
                output_file = os.path.join(base_dir, f"{sanitized_title}.pdf")

                downloaded = False
                if download_article(f'scidownl download --title "{title}" --out "{output_file}"', output_file):
                    downloaded = True
                elif doi and download_article(f'scidownl download --doi "{doi}" --out "{output_file}"', output_file):
                    downloaded = True
                else:
                    print(f"Ошибка: статья '{title}' не найдена.")

                if downloaded and os.path.exists(output_file):
                    sections_text = get_sections(output_file)
                    text = extract_text_from_pdf(output_file)

                    if sections_text:
                        introduction = sections_text.get('introduction') or sections_text.get('background')
                        results = sections_text.get('results') or sections_text.get('results and discussion')
                        discussion = sections_text.get('discussion')
                        conclusion = sections_text.get('conclusion') or sections_text.get('conclusions')
                        methods = sections_text.get('methods') or sections_text.get('materials') or sections_text.get(
                            'materials and methods')
                        keywords = sections_text.get('keywords')
                        references = sections_text.get('references')
            if method_list is []:
                method_check = []
            else:
                method_check = check_methods(methods, abstract, method_list)
            info.append({
                "title": title,
                "summary": summary,
                "authors": authors,
                "doi": doi,
                "publication_date": publication_date,
                "abstract": abstract,
                "text": text,
                "database": 'Google Scholar',
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
