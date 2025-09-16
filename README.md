
# 🧪 Research Agent — Multi-source Scholarly Search Assistant

**Research Agent** is a Python-based tool for searching scientific articles across multiple open sources  
(arXiv, Crossref, PubMed, HAL, DBLP, with optional OpenAlex).  

It retrieves metadata, scores relevance (with deterministic + optional Ollama LLM ranking), deduplicates,  
and saves per-paper results in **JSON**, with consolidated exports in **BibTeX** and **CSL-JSON**.

---

## ✨ Features

- 🔍 **Sources** (all open/free APIs):
  - [arXiv](https://arxiv.org/help/api) — abstracts, PDFs
  - [Crossref](https://api.crossref.org) — DOIs and publication metadata
  - [PubMed](https://www.ncbi.nlm.nih.gov/home/develop/api/) — biomedical articles
  - [HAL](https://api.archives-ouvertes.fr/) — French open archive
  - [DBLP](https://dblp.org/) — computer science publications
  - [OpenAlex](https://docs.openalex.org/) — optional (disable with `--no-openalex`)
- 🧹 **Deduplication** by DOI, arXiv ID, PubMed ID, HAL ID, DBLP ID, or title hash
- 🧮 **Relevance scoring**
  - Deterministic keyword overlap (fast, reliable)
  - Optional **semantic reranking** with a local LLM via [Ollama](https://ollama.com/) (e.g. `llama3.1:8b`)
- 📂 **Outputs**
  - One JSON per paper
  - Consolidated `index.jsonl`
  - Optional `export.bib` (BibTeX) and `export.csl.json` (CSL-JSON for citation managers)
- 📝 **Incremental saving**: results appear in `results/` as the agent runs
- ⚙️ Configurable: choose sources, year ranges, filters, and scoring thresholds

---

## 📦 Installation

```bash
git clone https://github.com/<your-username>/research-agent-vscode.git
cd research-agent-vscode

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
````

Optional: for semantic reranking or query expansion, install and run Ollama with your preferred model:

```bash
ollama pull llama3.1:8b
ollama run llama3.1:8b
```

---

## 🚀 Usage

### Basic search

```bash
python cli.py "graph neural networks chemistry" \
  --years 2021-2025 \
  --per-source 15 \
  --outdir results
```

### Disable some sources

```bash
python cli.py "language models healthcare" \
  --years 2020-2024 \
  --no-openalex --no-hal \
  --per-source 20 \
  --outdir results
```

### With Ollama reranking (semantic scoring)

```bash
python cli.py "diffusion models for medical imaging" \
  --years 2022-2025 \
  --per-source 30 \
  --ollama-model "llama3.1:8b" \
  --min-score 0.2 \
  --outdir results
```

### Export formats

```bash
python cli.py "graph neural networks chemistry" \
  --years 2021-2025 \
  --per-source 15 \
  --save-bibtex --save-csl \
  --outdir results
```

---

## 📂 Output Layout

```
results/
  graph-neural-networks-chemistry/
    index.jsonl         # one line per paper (summary)
    export.bib          # optional BibTeX
    export.csl.json     # optional CSL-JSON
    papers/
      a1b2c3d4e5f6.json # full metadata per paper
      ...
```

Example `papers/*.json`:

```json
{
  "title": "Diffusion Models for MRI Reconstruction",
  "abstract": "...",
  "year": 2023,
  "doi": "10.xxxx/abcd",
  "authors": ["Alice Smith", "Bob Jones"],
  "venue": "arXiv",
  "url_page": "https://arxiv.org/abs/...",
  "url_pdf": "https://arxiv.org/pdf/...",
  "score": 0.87,
  "source": "arxiv"
}
```

---

## ⚙️ Command-line Options

```
usage: cli.py [-h] 
              [--years YEARS] 
              [--per-source N]
              [--outdir PATH]
              [--ollama-model MODEL] 
              [--min-score FLOAT]
              [--max-papers N] 
              [--incremental]
              [--no-openalex] 
              [--no-arxiv] 
              [--crossref]
              [--no-pubmed] 
              [--no-hal] 
              [--no-dblp]
              [--save-bibtex] 
              [--save-csl]
              [--verbose]
              topic
```

Key flags:

* `--years`: filter year range (e.g. `2020-2024` or `2022`)
* `--per-source`: maximum results per source
* `--ollama-model`: enable LLM reranking (e.g. `llama3.1:8b`)
* `--min-score`: filter out low-relevance papers
* `--max-papers`: cap the number of saved papers
* `--incremental`: save results progressively during scoring
* `--save-bibtex`, `--save-csl`: export formats
* `--no-<source>`: disable specific sources
* `--verbose`: extra logging

---

## 🧪 Testing

```bash
pytest -q
```

---

## 🔮 Roadmap

* [ ] Add more sources (Scopus, IEEE Xplore, DOAJ, CORE, DOIs enrichment)
* [ ] Smarter reranking (diversification, clustering)
* [ ] Web dashboard (Streamlit/Gradio)
* [ ] Citation graph building (co-citation, reference mining)
* [ ] Integration with Zotero / Obsidian workflows

---

## 🤝 Contributing

1. Fork this repo
2. Create a branch (`git checkout -b feat/my-feature`)
3. Commit and push
4. Open a Pull Request

---

## 📌 Notes

* Some APIs (PubMed, HAL) have rate limits — large queries may need retries.
* OpenAlex may return 403 without a `mailto=` parameter; disable via `--no-openalex`.
* Google Scholar is **not supported** (scraping violates ToS). Use a legal provider like SerpAPI if needed.
* Results are incremental when `--incremental` is set, so you can inspect files as the run progresses.
