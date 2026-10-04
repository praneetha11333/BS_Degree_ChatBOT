# BS Degree ChatBOT

A RAG-based chatbot for the IITM BS Degree Student Handbook, built with hybrid retrieval and semantic caching.

## Architecture

```
source1.txt → chunk_stratergy.py → chunk_splitter.py → embed.py → qdrant
                                                                      ↓
                                                user query → app.py (hybrid retrieval + LLM)
```

## Files

| File | Purpose |
|------|---------|
| `extraction.py` | Fetches Google Docs and writes parsed output to `source1.txt` |
| `chunk_stratergy.py` | Parses `source1.txt` into chunks by section. Each chunk has `section`, `types`, `content`, `tables` |
| `chunk_splitter.py` | Splits chunks > 1000 tokens by row-wise table splitting |
| `embed.py` | Embeds chunks one by one using `text-embedding-3-small` and upserts into qdrant in batches |
| `semantic_cache.py` | In-memory semantic cache using cosine similarity to avoid redundant LLM calls |
| `app.py` | Streamlit UI with hybrid retrieval (dense + BM25 + RRF) and semantic caching |

## Setup

```bash
uv sync
```

Set `OPENAI_API_KEY` in `.env` (aipipe.org JWT token):
```
OPENAI_API_KEY=<your_aipipe_jwt>
```

## Usage

**1. Build the index (run once):**
```bash
uv run python embed.py
```

**2. Start the app:**
```bash
uv run streamlit run app.py
```

## Retrieval

Hybrid search combining:
- **Dense** — qdrant cosine similarity on `text-embedding-3-small` vectors
- **Sparse** — BM25 keyword matching for exact terms like course codes (`CS2001`, `EE2103`)
- **RRF** — Reciprocal Rank Fusion merges both rankings

## Chunking

- One chunk per `[SECTION:]` tag from `source1.txt`
- Tables stored as `{headers, rows}` list to handle multiple tables per section
- Chunks > 1000 tokens with tables are split every 12 rows (headers repeated per split)
- Max token limit: 8191 (`text-embedding-3-small`)

## Stack

- `qdrant` — vector store (local)
- `openai` — embeddings + LLM via aipipe.org
- `rank-bm25` — sparse retrieval
- `streamlit` — UI
- `uv` — package manager
