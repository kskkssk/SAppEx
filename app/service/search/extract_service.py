import os
import re
import time
import json
import torch
import pypdf
from openai import OpenAI
from collections import Counter
from sentence_transformers.util import cos_sim
from fast_sentence_transformers import FastSentenceTransformer as SentenceTransformer
import logging

API_KEY = os.getenv('GPT_API')
DICT_PATH = os.path.dirname(__file__)

sections = [
        'abstract', 'keywords', 'introduction', 'background', 'methods', 'materials and methods', 'methodology',
        'results', 'discussion', 'results and discussion',
        'conclusion', 'conclusions'
    ]


def sanitize_filename(title):
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', title)
    sanitized = sanitized.strip()[:100]
    return sanitized


def load_model(model_name="sentence-transformers/all-MiniLM-L6-v2"):
    try:
        #device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer(model_name)
        logging.info(f"Модель {model_name} успешно загружена.")
        return model
    except Exception as e:
        print(f"Ошибка при загрузке модели: {e}")
        return None


def vectorize_text(text):
    model = load_model()
    embeddings = model.encode(text)
    return list(embeddings)


def calculate_similarity(vec1, vec2):
    return round(float(cos_sim(vec1, vec2)), 3)


def extract_text_from_pdf(filepath):
    """Извлекает текст из PDF-файла, обрабатывает ошибки"""
    text = ""
    try:
        reader = pypdf.PdfReader(filepath)
        num_pages = len(reader.pages)
        text_list = []
        for page_num in range(num_pages):
            try:
                page_text = reader.pages[page_num].extract_text()
                if page_text:
                    text_list.append(page_text.strip())
                else:
                    print(f"⚠️ Страница {page_num + 1} не содержит текста")
            except Exception as e:
                print(f"Ошибка при обработке страницы {page_num + 1}: {e}")
        text = '\n'.join(text_list)
        text = text.replace('\xa0', ' ').replace('\x00', '')
    except FileNotFoundError:
        print(f"Файл {filepath} не найден.")
    except Exception as e:
        print(f"Общая ошибка при обработке файла {filepath}: {e}")
    return text


def preprocess(text):
    lower_text = text.lower()
    strings = lower_text.split('\n')
    return strings


def get_sections(filepath):
    section_texts = {}
    text = extract_text_from_pdf(filepath)

    pattern = re.compile(r"(?i)references|bibliography", re.DOTALL)
    match = pattern.search(text)
    if match:
        section_texts['references'] = text[match.start():].strip()
        text = text[:match.start()]

    strings = preprocess(text)

    section_embeddings = [vectorize_text(section) for section in sections]

    start_time = time.time()
    string_embeddings = [vectorize_text(string) for string in strings]
    end_time = time.time()
    print(f"Затраченное время {end_time - start_time}")

    for i, embeddings1 in enumerate(section_embeddings):
        for j, embeddings2 in enumerate(string_embeddings):
            sim = calculate_similarity(embeddings1, embeddings2)

            if sim > 0.7:
                print(sections[i])
                print(f"Similarity: {sim:.3f}")

                pattern = re.compile(re.escape(strings[j]), re.IGNORECASE)  # Экранируем спецсимволы
                match = pattern.search(text)

                if not match:
                    print(f"⚠️ Строка '{strings[j]}' не найдена в тексте!")
                    continue

                start = match.start()

                # Определяем границу следующей секции
                if i < len(sections) - 1:
                    next_section = sections[i + 1]
                    next_pattern = re.compile(re.escape(next_section), re.IGNORECASE)
                    next_match = next_pattern.search(text, start + len(strings[j]))

                    next_start = next_match.start() if next_match else len(text)
                else:
                    next_start = len(text)

                section_texts[sections[i]] = text[start:next_start].strip()
                last_end = next_start
                break  # Переход к следующей секции

    if 'keywords' not in section_texts:
        pattern = re.compile(
            r"Keywords:\s*(.*?)\s*(?=\n{0,2}(?:Author|Supporting|Introduction|Background|Accepted|1\. Introduction))",
            re.IGNORECASE | re.DOTALL
        )
        matches = pattern.findall(text)
        if matches:
            keywords = [match.replace("\n", " ").strip() for match in matches]
            section_texts['keywords'] = ", ".join(keywords)
    if 'abstract' not in section_texts:
        pattern = re.compile(
            r"Abstract\s*(.*?)\s*(?=\n{0,2}(?:Keywords|Introduction|Background))",
            re.IGNORECASE | re.DOTALL
        )
        match = pattern.search(text)
        if match:
            section_texts['abstract'] = match.group(1).strip()
    if 'materials and methods' in section_texts:
        if 'methods' in section_texts:
            del section_texts['methods']
    if 'methodology' in section_texts:
        if 'methods' in section_texts:
            del section_texts['methods']
    if 'results and discussion' in section_texts:
        if 'results' in section_texts:
            del section_texts['results']
        if 'discussion' in section_texts:
            del section_texts['discussion']
    if 'conclusions' in section_texts:
        if 'conclusion' in section_texts:
            del section_texts['conclusion']

    new_texts = section_texts.copy()

    keys = list(section_texts.keys())
    for i, key1 in enumerate(keys):
        for j, key2 in enumerate(keys):
            if i == j:
                continue

            text1 = section_texts[key1]
            text2 = section_texts[key2]

            overlap_index = text1.find(text2)

            if overlap_index != -1:  # Overlap found
                new_texts[key1] = text1[:overlap_index]

    return new_texts


def get_methods_dict():
    path = os.path.join(DICT_PATH, 'dictionary.json')
    with open(path, 'r', encoding='utf-8') as file:
        methods_dict = json.load(file)
    return methods_dict


def check_methods(methods, abstract, method_list):
    methods_dict = get_methods_dict()

    if not methods and not abstract:
        return False

    matched_keys = []
    for key, value in methods_dict.items():
        if key in method_list:
            if check_key_or_value(key, value, methods) or check_key_or_value(key, value, abstract):
                matched_keys.append(key)
    return matched_keys if matched_keys else False


def check_key_or_value(key, value, check_list):
    """ Функция проверки наличия ключа или значения в списке """
    if not check_list:
        return False
    if key in check_list:
        return True
    if isinstance(value, list):
        return any(val in check_list for val in value)
    return value in check_list if isinstance(value, str) else False


def authors_count(text):
    pattern = re.compile(r'([A-Z][a-z]+),\s*([A-Z](?:\.\s*[A-Z]\.)*)')
    authors = []
    text = text.split('\n')
    for ref in text:
        matches = pattern.findall(ref)
        for match in matches:
            author = f"{match[0]} {match[1]}"  # Объединяем фамилию и инициалы
            authors.append(author)
    return dict(Counter(authors))


def send_text_chunks_to_gpt(text):
    client = OpenAI(
        api_key=API_KEY,
    )
    content = "-"
    try:
        first_response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:pygmalion::BJJMGKNu",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник, который структурирует экспериментальные данные из научных текстов."
                },
                {
                    "role": "user",
                    "content": f"""Выведи методики из научной статьи по шаблону 1. Название методики; Объект; Оборудование; Материалы; Процедура; Результаты(если есть для этой методики). Используй этот текст: {text}"""
                }
            ]
        )
        # Обратите внимание на эту строку:
        content = first_response.choices[0].message.content
        print(content)
    except Exception as e:
        print(f"Ошибка при обработке чанка {text}: {e}")
    return content
