# Utilities: slugify, hashing, JSON writing, simple keyword scoring, and a tiny Ollama client.
from __future__ import annotations
import re, hashlib, os, json

def slugify(text: str) -> str:
    """
    Convert topic text to a filesystem-friendly slug:
    - lowercase
    - keep alphanumerics and spaces/dashes
    - replace spaces with hyphens
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\- ]+", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text or "topic"

def safe_hash(text: str) -> str:
    """Stable short id for filenames (first 16 hex of SHA-256)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def ensure_dir(path: str) -> None:
    """Create directory if missing."""
    os.makedirs(path, exist_ok=True)

def write_json(path: str, data: dict) -> None:
    """Write JSON with UTF-8 and indentation."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def simple_content_score(query: str, text: str) -> float:
    """
    Deterministic relevance based on keyword overlap:
    score = |tokens(query) ∩ tokens(text)| / |tokens(query)|
    - tokens are alphanumeric words (>=3 characters)
    - returns 0..1
    """
    if not query or not text:
        return 0.0
    qtoks = set([t for t in re.findall(r"[a-zA-Z0-9]+", query.lower()) if len(t) > 2])
    ttoks = set([t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) > 2])
    if not qtoks or not ttoks:
        return 0.0
    inter = len(qtoks & ttoks)
    return inter / len(qtoks)

class OllamaClient:
    """
    Lightweight wrapper:
    - uses python `ollama` package if present
    - otherwise falls back to HTTP on localhost:11434
    - classification prompt must produce JSON: {"score": float in [0,1]}
    """
    def __init__(self, model: str = "llama3.1:8b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")
        self._use_pkg = False
        try:
            import ollama  # type: ignore
            self._ollama = ollama
            self._use_pkg = True
        except Exception:
            self._ollama = None

    def classify_relevance(self, query: str, abstract: str) -> float:
        """
        Ask a local LLM to rate abstract relevance [0..1].
        If anything fails, we fall back to simple_content_score.
        """
        if not query or not abstract:
            return 0.0
        prompt = (
            "Rate from 0.0 to 1.0 how relevant the following paper abstract is "
            "to the user's query. Return ONLY a JSON object like {\"score\": 0.0}.\n\n"
            f"Query: {query}\n\nAbstract:\n{abstract}\n"
        )
        try:
            if self._use_pkg:
                resp = self._ollama.generate(
                    model=self.model, prompt=prompt, options={"temperature": 0.0, "num_predict": 64}
                )
                txt = resp.get("response","")
            else:
                import requests, json as _json
                url = f"{self.host}/api/generate"
                payload = {"model": self.model, "prompt": prompt,
                           "options":{"temperature":0.0,"num_predict":64}, "stream": False}
                r = requests.post(url, json=payload, timeout=60)
                r.raise_for_status()
                txt = r.json().get("response","")
            s = txt.find("{"); e = txt.rfind("}")
            if s!=-1 and e!=-1:
                import json as _json
                data = _json.loads(txt[s:e+1])
                val = float(data.get("score", 0.0))
                return max(0.0, min(1.0, val))
        except Exception:
            pass
        return simple_content_score(query, abstract)
