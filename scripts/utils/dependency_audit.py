"""
Dependency Audit Script
=======================

Purpose:
    Scan the `coda/` Django project for **cross-app imports** and emit
    a structured report showing which apps depend on which other apps,
    and via which modules.

Usage:
    From the project root:

        source venv/bin/activate
        python scripts/dependency_audit.py

Output:
    - Human‑readable summary grouped by source app
    - Optional CSV‑style summary (stdout) if --csv is passed

Notes:
    - Only imports under the `coda/` package are analyzed.
    - The script infers "apps" from subdirectories of `coda/` that
      contain an `apps.py` file.
    - A "cross‑app" import is any import where:
        importing_app != imported_app
      and both are recognized apps.
"""

import ast
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODA_ROOT = os.path.join(PROJECT_ROOT, "coda")


@dataclass(frozen=True)
class ImportEdge:
    """Represents a single cross‑app import."""

    src_app: str
    dst_app: str
    filename: str
    module: str
    imported_names: Tuple[str, ...]


def discover_apps(coda_root: str) -> Set[str]:
    """
    Discover Django apps by looking for subdirectories with an `apps.py` file.

    Returns a set of app module names (e.g. "finance", "management").
    """
    apps: Set[str] = set()
    if not os.path.isdir(coda_root):
        return apps

    for entry in os.listdir(coda_root):
        full_path = os.path.join(coda_root, entry)
        if not os.path.isdir(full_path):
            continue
        apps_py = os.path.join(full_path, "apps.py")
        if os.path.isfile(apps_py):
            apps.add(entry)
    return apps


def infer_app_from_path(filepath: str) -> Optional[str]:
    """
    Given an absolute or project‑relative path, infer the app name by taking
    the first component under `coda/`.
    """
    # Normalize to project‑relative path
    rel = os.path.relpath(filepath, PROJECT_ROOT)
    parts = rel.replace("\\", "/").split("/")
    try:
        coda_index = parts.index("coda")
    except ValueError:
        return None
    if len(parts) <= coda_index + 1:
        return None
    return parts[coda_index + 1]


def walk_python_files(root: str) -> Iterable[str]:
    """Yield all .py files under the given root."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip typical noise directories
        dirnames[:] = [
            d
            for d in dirnames
            if d not in {"__pycache__", "migrations", "static", "templates"}
        ]
        for fname in filenames:
            if fname.endswith(".py"):
                yield os.path.join(dirpath, fname)


def parse_imports_from_source(src: str) -> List[ast.stmt]:
    """Parse Python source and return top‑level statements (or empty on failure)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    return [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]


def extract_cross_app_imports(
    filepath: str,
    src_app: Optional[str],
    known_apps: Set[str],
) -> List[ImportEdge]:
    """
    Extract cross‑app imports from a single file.

    Returns a list of ImportEdge entries.
    """
    if src_app is None or src_app not in known_apps:
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            src = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    stmts = parse_imports_from_source(src)
    edges: List[ImportEdge] = []

    for stmt in stmts:
        if isinstance(stmt, ast.ImportFrom):
            if stmt.module is None:
                continue
            module = stmt.module
            top_level = module.split(".")[0]
            if top_level in known_apps and top_level != src_app:
                imported_names = tuple(
                    alias.name for alias in stmt.names if isinstance(alias, ast.alias)
                )
                edges.append(
                    ImportEdge(
                        src_app=src_app,
                        dst_app=top_level,
                        filename=os.path.relpath(filepath, PROJECT_ROOT),
                        module=module,
                        imported_names=imported_names,
                    )
                )
        elif isinstance(stmt, ast.Import):
            # Handle "import finance.models" style imports (less common here)
            for alias in stmt.names:
                name = alias.name
                top_level = name.split(".")[0]
                if top_level in known_apps and top_level != src_app:
                    edges.append(
                        ImportEdge(
                            src_app=src_app,
                            dst_app=top_level,
                            filename=os.path.relpath(filepath, PROJECT_ROOT),
                            module=name,
                            imported_names=(alias.asname or alias.name,),
                        )
                    )

    return edges


def build_dependency_graph() -> List[ImportEdge]:
    """Scan the codebase and return all cross‑app ImportEdge entries."""
    known_apps = discover_apps(CODA_ROOT)
    if not known_apps:
        print("No apps discovered under `coda/`. Is the project structure correct?")
        return []

    edges: List[ImportEdge] = []
    for pyfile in walk_python_files(CODA_ROOT):
        src_app = infer_app_from_path(pyfile)
        file_edges = extract_cross_app_imports(pyfile, src_app, known_apps)
        edges.extend(file_edges)
    return edges


def summarize_human_readable(edges: List[ImportEdge]) -> None:
    """Print a human‑readable summary grouped by source app."""
    if not edges:
        print("No cross‑app imports found.")
        return

    by_src: Dict[str, List[ImportEdge]] = defaultdict(list)
    for e in edges:
        by_src[e.src_app].append(e)

    print("\n=== Cross‑App Dependency Report ===\n")
    for src_app in sorted(by_src.keys()):
        app_edges = by_src[src_app]
        dst_apps: Dict[str, int] = defaultdict(int)
        for e in app_edges:
            dst_apps[e.dst_app] += 1

        print(f"App: {src_app}")
        print("  Depends on:")
        for dst, count in sorted(dst_apps.items()):
            print(f"    - {dst} (imports: {count})")
        print("  Details:")
        for e in sorted(app_edges, key=lambda x: (x.dst_app, x.filename, x.module)):
            imported = ", ".join(e.imported_names) if e.imported_names else "(*)"
            print(
                f"    - {e.filename}: from {e.module} import {imported} "
                f"-> {e.dst_app}"
            )
        print()


def summarize_csv(edges: List[ImportEdge]) -> None:
    """Print a simple CSV summary: src_app,dst_app,filename,module,imported_names."""
    print("src_app,dst_app,filename,module,imported_names")
    for e in edges:
        imported = "|".join(e.imported_names)
        # Basic CSV‑safe escaping (no embedded commas expected in these fields)
        print(f"{e.src_app},{e.dst_app},{e.filename},{e.module},{imported}")


def main(argv: List[str]) -> int:
    csv_mode = "--csv" in argv
    edges = build_dependency_graph()
    if csv_mode:
        summarize_csv(edges)
    else:
        summarize_human_readable(edges)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))





