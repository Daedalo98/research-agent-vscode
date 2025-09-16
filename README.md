# 🧪 Research Agent — Multi-source Scholarly Search Assistant

**Research Agent** is a Python-based tool for searching scientific articles across multiple open sources  
(arXiv, Crossref, PubMed, HAL, DBLP, with optional OpenAlex).  

It retrieves metadata, deduplicates results, scores them by relevance (deterministic and/or with a local LLM),  
and saves per-paper results in **JSON**, with consolidated exports in **BibTeX** and **CSL-JSON** (enabled by default).

---

## ✨ Features

- 🔍 **Sources**:
  - [arXiv](https://arxiv.org/help/api) — preprints (title, abstract, PDF)
  - [Crossref](https://api.crossref.org) — DOIs and journal metadata
  - [PubMed](https://www.ncbi.nlm.nih.gov/home/develop/api/) — biomedical research
  - [HAL](https://api.archives-ouvertes.fr/) — French open archive
  - [DBLP](https://dblp.org/) — computer science bibliography
  - [OpenAlex](https://docs.openalex.org/) — optional (disable with `--no-openalex`)
- 🧹 **Deduplication**: DOI → arXiv ID → PubMed ID → HAL ID → DBLP ID → title hash
- 🧮 **Relevance scoring**:
  - Deterministic keyword overlap (fast, reliable)
  - Optional **semantic reranking** with a local Ollama model (e.g. `llama3.1:8b`)
- 📂 **Outputs**:
  - One JSON per paper (`papers/*.json`)
  - Consolidated `index.jsonl`
  - `export.bib` (BibTeX, default)
  - `export.csl.json` (CSL-JSON, default for Zotero/CSL-compatible tools)
- 📝 **Incremental saving**: results appear progressively during scoring

---

## 📦 Installation

```bash
git clone https://github.com/<your-username>/research-agent-vscode.git
cd research-agent-vscode

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
````

Optional (for LLM reranking):

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

### With semantic reranking (Ollama)

```bash
python cli.py "diffusion models for medical imaging" \
  --years 2022-2025 \
  --per-source 30 \
  --ollama-model "llama3.1:8b" \
  --min-score 0.2 \
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

### Disable exports (BibTeX or CSL)

Exports are **enabled by default**. Disable with:

```bash
python cli.py "graph neural networks chemistry" \
  --years 2021-2025 \
  --per-source 15 \
  --no-bibtex --no-csl \
  --outdir results
```

---

## 📂 Output Layout

```
results/
  graph-neural-networks-chemistry/
    index.jsonl         # one line per paper (summary)
    export.bib          # BibTeX (default)
    export.csl.json     # CSL-JSON (default)
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
usage: cli.py [-h] [--years YEARS] [--per-source PER_SOURCE]
              [--outdir OUTDIR] [--ollama-model OLLAMA_MODEL]
              [--min-score MIN_SCORE] [--max-papers MAX_PAPERS]
              [--no-openalex] [--no-arxiv] [--crossref]
              [--no-pubmed] [--no-hal] [--no-dblp]
              [--use-doaj] [--use-core] [--use-scopus] [--use-ieee]
              [--no-bibtex] [--no-csl]
              [--verbose] [--incremental]
              topic
```

Key flags:

* `--years`: year filter (`YYYY` or `YYYY-YYYY`)
* `--per-source`: max results per source
* `--ollama-model`: use Ollama LLM for reranking (e.g. `llama3.1:8b`)
* `--min-score`: filter out low-relevance papers
* `--max-papers`: cap number of saved papers
* `--no-<source>`: disable a source
* `--use-doaj`, `--use-core`, `--use-scopus`, `--use-ieee`: enable additional sources (experimental / API key required)
* `--no-bibtex`, `--no-csl`: disable exports (default ON)
* `--incremental`: save results progressively
* `--verbose`: detailed logging

---

## 🧪 Testing

```bash
pytest -q
```

---

## 🔮 Roadmap

* [ ] Add more sources (DOAJ, CORE, Scopus, IEEE Xplore, DOIs enrichment)
* [ ] Smarter reranking (diversification, clustering)
* [ ] Web dashboard (Streamlit/Gradio)
* [ ] Citation graph building (co-citation, reference mining)
* [ ] Integration with Zotero / Obsidian workflows
* [ ] RIS export for EndNote/Mendeley

---

## 🤝 Contributing

1. Fork this repo
2. Create a branch (`git checkout -b feat/my-feature`)
3. Commit and push
4. Open a Pull Request

---

## 📌 Notes

* Some APIs (PubMed, HAL) have rate limits — large queries may need retries.
* OpenAlex may return `403` without `mailto`; disable via `--no-openalex`.
* Google Scholar is **not supported** (scraping violates ToS). Use a legal provider (e.g., SerpAPI) if needed.
* Exports (`export.bib` and `export.csl.json`) are written automatically after each run.