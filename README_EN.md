# SAppEx
# SAppEx — Semantic Search & Experiment Extraction for Scientific Papers

SAppEx (Search App for Experimenters) is an AI-powered system for **automated search, segmentation, and analysis of scientific publications**.
The service significantly reduces the time required to find relevant experimental methodologies in large scientific databases.

SAppEx combines **semantic search, NLP, vector embeddings, and LLM-based extraction** to help researchers quickly identify relevant papers and experimental procedures.

---

## Key Features

- **Multi-source Scientific Search**
  - Google Scholar (via SerpAPI)
  - PubMed Central (full-text access)
  - Automatic deduplication by title and DOI

- **Semantic Search & Filtering**
  - Search by query, publication date, and document type
  - Optional filtering by experimental methods and techniques
  - Author popularity–based ranking

- **Automatic PDF Processing**
  - PDF parsing and text extraction
  - Robust handling of multi-column scientific PDFs

- **Section Segmentation**
  - Automatic extraction of key paper sections:
    - Abstract
    - Methods / Materials and Methods
    - Results
    - Discussion
  - Hybrid approach:
    - Regex-based heuristics
    - Semantic similarity with **Sentence Transformers**
  - Optimized inference using **Fast Sentence Transformers (ONNX + INT8 quantization)**

- **LLM-Based Experiment Extraction**
  - Extraction of structured experimental procedures from selected sections
  - Fine-tuned **GPT-4o-mini** model for:
    - Method name
    - Object
    - Materials
    - Equipment
    - Step-by-step procedure
    - Results

---

## Performance & Evaluation

- Section segmentation metrics:
  - **Macro Precision ≈ 89%**
  - **Macro Recall ≈ 82%**
  - **Macro F1 ≈ 85%**
- Average processing time per article: **4–11 seconds**
- Reduces manual literature review from **~1 week to ~25 minutes**

---

## System Architecture

- **Backend:** FastAPI (async)
- **Reverse Proxy:** Nginx
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Caching / Background tasks:** Redis
- **ML / NLP:**
  - SentenceTransformers (`all-MiniLM-L6-v2`)
  - Fast Sentence Transformers (ONNX, INT8)
  - Fine-tuned GPT-4o-mini
- **Deployment:** Docker + Docker Compose

---

## Data Flow

1. User submits a query
2. Papers collected from multiple sources
3. PDFs downloaded and parsed
4. Text segmented into logical sections
5. Semantic filtering and ranking applied
6. LLM extracts structured experimental data
7. User receives:
   - PDF files
   - Excel report with metadata, sections, authors, and extracted methods

---

## Output Formats

- **ZIP archive** containing:
  - PDF files of selected publications
  - Excel report with:
    - Article metadata
    - Extracted sections
    - Author statistics
    - Structured experimental methodologies
- Optional **DOCX report** for curated results

---

## Tech Stack

- Python
- FastAPI
- Nginx
- PostgreSQL
- SQLAlchemy
- Redis
- SentenceTransformers
- Fast Sentence Transformers (ONNX, INT8)
- OpenAI API (LLM fine-tuning)
- Docker / Docker Compose

---

## Highlights (for recruiters / startups)

- End-to-end AI system for scientific knowledge extraction
- Combination of classical NLP, embeddings, and LLMs
- Optimized inference without mandatory GPU usage
- Production-ready backend with async processing
- Real-world scientific validation on chemistry use cases

---

## Repository Structure

- `parser` — scientific data collection (PubMed, Google Scholar)
- `nlp` — text segmentation and embeddings
- `llm` — experiment extraction and fine-tuning
- `backend` — FastAPI service
- `db` — database models and persistence
- `docker` — deployment configuration
