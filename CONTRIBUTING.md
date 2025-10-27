# Contributing

## Setup
1. Create a venv and install deps:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   pip install pytest ruff pre-commit
   ```
2. Install git hooks:
   ```bash
   pre-commit install
   ```

## Dev Tasks
- Run the app: `streamlit run app.py`
- Lint/format: `ruff check .` / `ruff format .`
- Tests: `pytest`

## Pull Requests
- Keep PRs small and focused.
- Include tests for behavioral changes.
