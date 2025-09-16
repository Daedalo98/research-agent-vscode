# 🧪 Research Agent

A **local-first scientific search assistant** that queries **arXiv**, **Crossref**, and optionally **OpenAlex**,  
then scores the results by content relevance (abstract, not just titles) and saves **one JSON per paper** for reproducible research.

Supports **optional local LLM reranking** via [Ollama](https://ollama.com/) (e.g. `llama3:8b`) to improve semantic matching.

---

## ✨ Features

- 🔍 Search **arXiv** (open API), **Crossref** (journal DOIs), and optionally **OpenAlex**  
- 📑 Collect **title, authors, year, DOI, venue, abstract, links**  
- 🧮 Relevance scoring:
  - keyword overlap (fast, deterministic)
  - optional local Ollama LLM (semantic)
- 🗂️ Output:
  - one **JSON per paper** in `results/<topic-slug>/papers/*.json`
  - consolidated **`index.jsonl`** for quick processing
- 🧹 Deduplication by DOI / arXiv ID / title hash
- ⚡ No cloud lock-in — runs fully local, or can call external APIs if available

---

## 📦 Installation

Clone and set up a virtual environment:

```bash
git clone https://github.com/<your-username>/research-agent-vscode.git
cd research-agent-vscode

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 🚀 Usage

Basic search (arXiv + Crossref):

```bash
python cli.py "diffusion models for medical imaging" \
  --years 2022-2025 \
  --per-source 50 \
  --min-score 0.2 \
  --outdir results
```

Using **Ollama reranking** (ensure Ollama is running and model is installed):

```bash
ollama run llama3:8b  # warm up model

python cli.py "diffusion models for medical imaging" \
  --years 2022-2025 \
  --per-source 50 \
  --ollama-model "llama3:8b" \
  --min-score 0.3 \
  --outdir results
```

Disable OpenAlex if it gives 403s:

```bash
python cli.py "large language models biology" --no-openalex
```

---

## 📂 Output Layout

Example run:

```
results/
  diffusion-models-for-medical-imaging/
    index.jsonl         # one line per paper (summary)
    papers/
      1a2b3c4d5e6f.json # full metadata for each paper
      ...
```

Each `papers/*.json` contains:

```json
{
  "title": "...",
  "abstract": "...",
  "year": 2023,
  "doi": "10.xxxx/abcd",
  "authors": ["Alice Smith", "Bob Jones"],
  "venue": "arXiv",
  "url_page": "https://arxiv.org/abs/...",
  "url_pdf": "https://arxiv.org/pdf/...",
  "score": 0.87,
  "source": "arxiv",
  "source_payload": { ... }   // raw API data
}
```

---

## ⚙️ Command-line Options

```
usage: cli.py [-h] [--years YEARS] [--per-source N]
              [--outdir PATH] [--ollama-model MODEL]
              [--min-score FLOAT] [--max-papers N]
              [--crossref] [--no-openalex]
              topic
```

* `topic` — research query, e.g. `"graph neural networks chemistry"`
* `--years` — single year (`2023`) or range (`2020-2024`)
* `--per-source` — max results per source (default: 50)
* `--outdir` — results directory (default: `results/`)
* `--ollama-model` — enable local LLM reranking, e.g. `"llama3:8b"`
* `--min-score` — filter out low-relevance papers (0..1)
* `--max-papers` — cap final saved papers
* `--crossref` — include Crossref results
* `--no-openalex` — skip OpenAlex

---

## 🧪 Testing

Run the test suite:

```bash
pytest -q
```

---

## 🔧 Development

Format & lint:

```bash
black src
ruff check src
```

Run smoke test:

```bash
python cli.py "quantum computing cryptography" --years 2020-2024 --per-source 10 --min-score 0.0
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/new-source`)
3. Commit your changes
4. Push and open a PR

Ideas welcome: add new sources (PubMed, HAL, etc.), export formats (BibTeX, CSL), PDF fetching, or a web UI.

---

## 📌 Notes

* Google Scholar scraping is not supported (violates ToS). For Scholar-like results, use a legal API (e.g. SerpAPI).
* OpenAlex sometimes returns `403` if User-Agent or `mailto` is missing. You can set `export OPENALEX_MAILTO="you@example.com"`.
* For large queries, be mindful of API rate limits.

---

```