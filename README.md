# Python Code Explainer (Streamlit)

Paste Python, get a structured explanation. Optionally run in a minimal sandbox and toggle LLM mode for a richer walkthrough.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# optional
export OPENAI_API_KEY=YOUR_KEY   # Windows: set OPENAI_API_KEY=YOUR_KEY
streamlit run app.py
```

## Features
- **Offline explainer**: AST-based structure (no API key required).
- **LLM explainer**: Toggle on for step-by-step, beginner-friendly narration.
- **Sandboxed run**: Restricted builtins + static checks (educational, not hardened).

---
## Dev Quality
- Lint: `ruff check .` • Format: `ruff format .` • Tests: `pytest`
- Pre-commit hooks: `pre-commit install`

## CI
GitHub Actions runs Ruff + Pytest on every push/PR (`.github/workflows/ci.yml`).

## Security Notes
No imports or system access in sandbox; treat as educational, not a hardened sandbox.
