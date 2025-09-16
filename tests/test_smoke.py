# Tiny sanity checks for utils (run: pytest -q)
from src.research_agent.utils import simple_content_score, slugify

def test_utils_basic():
    s = simple_content_score("diffusion models medical imaging", "We study diffusion models for MRI reconstruction.")
    assert 0.0 <= s <= 1.0
    assert slugify("Hello, World!") == "hello-world"
