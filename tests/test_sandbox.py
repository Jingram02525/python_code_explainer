import importlib.util
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("app", APP)
app = importlib.util.module_from_spec(spec)  # type: ignore
assert spec and spec.loader
spec.loader.exec_module(app)  # type: ignore

def test_sandbox_allows_simple_print():
    out = app.sandbox_run("print(2 + 2)")
    assert out.strip() == "4"

def test_sandbox_blocks_imports():
    try:
        app.sandbox_run("import os")
        assert False, "Expected import to be blocked"
    except app.SafetyError:
        assert True

def test_sandbox_blocks_dangerous_calls():
    bad = "open('secret.txt','w')"
    try:
        app.sandbox_run(bad)
        assert False, "Expected open() to be blocked"
    except app.SafetyError:
        assert True
