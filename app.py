import ast
import io
import os
from contextlib import redirect_stdout

import streamlit as st

# --- App title & intro ---
st.set_page_config(page_title="Python Code Explainer", page_icon="🐍")
st.title("🐍 Python Code Explainer")
st.caption("Paste Python, get a step‑by‑step explanation. Optional: run your snippet in a minimal sandbox.")

# --- Helpers: AST analysis and sandboxed execution ---

DANGEROUS_NAMES = {
    "exec", "eval", "__import__", "open", "compile",
    "input", "help", "license", "credits",
    "os", "sys", "subprocess", "shutil", "pathlib", "socket", "requests"
}

DANGEROUS_ATTR_PARENTS = {"os", "sys", "subprocess", "shutil", "pathlib", "socket"}

ALLOWED_BUILTINS = {
    "print": print,
    "range": range,
    "len": len,
    "enumerate": enumerate,
    "sum": sum,
    "min": min,
    "max": max,
    "sorted": sorted,
    "abs": abs,
    "any": any,
    "all": all,
    "zip": zip,
}

class SafetyError(Exception):
    pass

def static_checks(tree: ast.AST):
    """Reject obviously unsafe code constructs."""
    for node in ast.walk(tree):
        # Import statements
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SafetyError("Imports are not allowed in sandbox mode.")
        # Calls to dangerous builtins by name
        if isinstance(node, ast.Call):
            # Direct name calls (e.g., eval(...))
            if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_NAMES:
                raise SafetyError(f"Use of '{node.func.id}()' is not allowed in sandbox mode.")
            # Attribute calls (e.g., os.system(...), sys.argv.__class__(), etc.)
            if isinstance(node.func, ast.Attribute):
                # x.y(...), flag if parent x is a dangerous module name
                if isinstance(node.func.value, ast.Name) and node.func.value.id in DANGEROUS_ATTR_PARENTS:
                    raise SafetyError(f"Access to '{node.func.value.id}.{node.func.attr}()' is not allowed in sandbox mode.")
        # Attribute access like os.path, sys.modules, etc.
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in DANGEROUS_ATTR_PARENTS:
                raise SafetyError(f"Access to '{node.value.id}.{node.attr}' is not allowed in sandbox mode.")
        # With / AsyncWith (could open files, etc.) — conservatively disallow
        if isinstance(node, (ast.With, ast.AsyncWith)):
            raise SafetyError("with/async with blocks are not allowed in sandbox mode.")
        # Try/Except is okay for learning, but can hide attacks; allow it.

def analyze_code_structure(tree: ast.AST) -> dict:
    """Collect simple structural facts for an offline explanation."""
    info = {
        "functions": [],
        "classes": [],
        "assignments": 0,
        "loops": 0,
        "conditionals": 0,
        "returns": 0,
        "calls": set(),
        "imports": 0,
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            params = [a.arg for a in node.args.args]
            info["functions"].append({"name": node.name, "params": params})
        elif isinstance(node, ast.ClassDef):
            info["classes"].append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            info["assignments"] += 1
        elif isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
            info["loops"] += 1
        elif isinstance(node, ast.If):
            info["conditionals"] += 1
        elif isinstance(node, ast.Return):
            info["returns"] += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            info["imports"] += 1
        elif isinstance(node, ast.Call):
            # record function name when obvious
            if isinstance(node.func, ast.Name):
                info["calls"].add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.attr, str):
                    info["calls"].add(node.func.attr)
    info["calls"] = sorted(info["calls"])
    return info

def sandbox_run(code: str) -> str:
    """Run code with restricted builtins, capture stdout."""
    tree = ast.parse(code, mode="exec")
    static_checks(tree)
    bytecode = compile(tree, filename="<sandbox>", mode="exec")
    safe_globals = {"__builtins__": ALLOWED_BUILTINS}
    safe_locals = {}
    buf = io.StringIO()
    with redirect_stdout(buf):
        exec(bytecode, safe_globals, safe_locals)
    return buf.getvalue()

def offline_explain(code: str) -> str:
    """Generate a simple, deterministic explanation using AST structure."""
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return f"Syntax error on line {e.lineno}: {e.msg}"
    info = analyze_code_structure(tree)
    lines = []
    lines.append("**What I see (offline analysis):**")
    if info["functions"]:
        fn_list = ", ".join(f"{f['name']}({', '.join(f['params'])})" for f in info['functions'])
        lines.append(f"- Functions defined: {fn_list}")
    if info["classes"]:
        lines.append(f"- Classes defined: {', '.join(info['classes'])}")
    lines.append(f"- Assignments: {info['assignments']}  •  Loops: {info['loops']}  •  If/Elif/Else blocks: {info['conditionals']}  •  Returns: {info['returns']}")
    if info["calls"]:
        lines.append(f"- Calls detected: {', '.join(info['calls'])}")
    if info["imports"]:
        lines.append(f"- Imports present: {info['imports']} (won't run in sandbox)")

    # Heuristic: Big-O hints (very rough)
    big_o = "O(1) to O(n) typical"
    if info["loops"] >= 2:
        big_o = "O(n·m) or O(n²) depending on nesting"
    lines.append(f"- Complexity (rough heuristic): {big_o}")

    # Tips
    lines.append("\n**Tips:**")
    lines.append("- Add docstrings to functions to clarify intent.")
    lines.append("- Prefer list comprehensions or generator expressions where it makes code clearer.")
    lines.append("- Keep I/O separate from pure logic to simplify testing.")
    return "\n".join(lines)

# --- Optional: LLM explanation (uses OpenAI if key available) ---

def llm_explain(code: str) -> str:
    """Explain code with an LLM if OPENAI_API_KEY is set, else fallback."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        # OpenAI SDK v1
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        system = (
            "You are a precise yet friendly Python tutor. "
            "Explain code step-by-step, annotate lines, highlight pitfalls, and suggest small refactors. "
            "Keep it concise and actionable."
        )
        user = (
            "Explain this Python code for a beginner:\n\n"
            f"{code}\n\n"
            "Format:\n"
            "1) Summary (2–3 sentences)\n"
            "2) Step-by-step walkthrough (bullets)\n"
            "3) Key concepts learned\n"
            "4) Potential bugs / edge cases\n"
            "5) Tiny refactor suggestions"
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"(LLM explanation unavailable: {e})"

# --- UI ---

DEFAULT_SNIPPET = """def gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

print(gcd(42, 30))
"""

code = st.text_area("Paste Python code here:", value=DEFAULT_SNIPPET, height=240, label_visibility="visible")

col1, col2, col3 = st.columns(3)
with col1:
    explain = st.button("🧠 Explain")
with col2:
    run = st.button("▶️ Run (sandboxed)")
with col3:
    use_llm = st.checkbox("Use LLM (requires OPENAI_API_KEY)", value=False)

if explain:
    if use_llm:
        out = llm_explain(code)
        if out:
            st.markdown(out)
        else:
            st.markdown(offline_explain(code))
    else:
        st.markdown(offline_explain(code))

if run:
    try:
        output = sandbox_run(code)
        if output.strip() == "":
            st.info("Program ran with no output.")
        else:
            st.code(output, language="text")
    except SafetyError as se:
        st.error(f"Safety check failed: {se}")
    except SyntaxError as e:
        st.error(f"Syntax error on line {e.lineno}: {e.msg}")
    except Exception as e:
        st.exception(e)

st.divider()
with st.expander("How this sandbox works (and its limits)"):
    st.write("""
- Disallows imports, file/network/system access, and dangerous builtins like `eval`, `exec`, and `open`.
- Provides a tiny set of safe builtins: `print`, `range`, `len`, `enumerate`, `sum`, `min`, `max`, `sorted`, `abs`, `any`, `all`, `zip`.
- Uses Python's `ast` to statically check for risky nodes, then executes with restricted builtins.
- This is **not** a perfect security boundary. Treat it as a classroom demo, not a production sandbox.
""")
