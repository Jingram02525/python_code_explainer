# Python Code Explainer (Streamlit)

A tiny app you can build in minutes: paste Python, get a structured explanation. Optionally run the snippet in a minimal sandbox. Optionally use an LLM for richer explanations.

## Quickstart

```bash
# 1) Create & activate a virtualenv (recommended)
python3 -m venv .venv && source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) (Optional) Use an LLM for richer explanations
export OPENAI_API_KEY=YOUR_KEY_HERE   # on Windows: set OPENAI_API_KEY=YOUR_KEY_HERE

# 4) Run
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## Features
- **Offline explainer**: AST-based structural summary (no API key required).
- **LLM explainer**: Toggle on for step-by-step, beginner-friendly narration.
- **Sandboxed run**: Executes code with restricted builtins and static checks.
- **Teaching-friendly**: Shows structure, calls, loops, and rough complexity hints.

## Notes
- The sandbox is intentionally conservative. No imports, file or network access.
- For the LLM mode, you can edit the model name in `app.py` if desired.
