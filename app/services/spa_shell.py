"""Helpers to serve the compiled SPA shell from FastAPI routes."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from fastapi.responses import HTMLResponse

BASE_DIR = Path(__file__).resolve().parents[2]

# SvelteKit adapter-static output → build/200.html (fallback SPA shell)
# During deploy, build/ contents are copied to static/spa/
SPA_INDEX_PATH = BASE_DIR / "static" / "spa" / "200.html"
# Fallback to legacy index.html if 200.html not found yet
SPA_INDEX_PATH_LEGACY = BASE_DIR / "static" / "spa" / "index.html"


def _get_spa_path() -> Path:
    """Return the SPA shell path, preferring SvelteKit 200.html over legacy index.html."""
    if SPA_INDEX_PATH.exists():
        return SPA_INDEX_PATH
    return SPA_INDEX_PATH_LEGACY


def render_spa_shell(default_route: str, globals_map: Mapping[str, str] | None = None) -> HTMLResponse:
    """
    Return the built SPA shell HTML.

    With SvelteKit file-based routing, the shell no longer needs hash-based
    bootstrap. We still inject ``window.__ERP_BOOTSTRAP__`` for backward
    compatibility with any component that reads it.
    """
    spa_path = _get_spa_path()

    if not spa_path.exists():
        return HTMLResponse(
            content=(
                "<h1>SPA build no disponible</h1>"
                "<p>Ejecuta <code>cd frontend && npm run build</code> y copie build/ a static/spa/.</p>"
            ),
            status_code=503,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    html = spa_path.read_text(encoding="utf-8")

    # Inject minimal bootstrap for backward compat (no hash redirect needed)
    bootstrap_entries = [f"defaultRoute: '{default_route}'"]
    if globals_map:
        for key, value in globals_map.items():
            safe_key = key.replace("'", "")
            safe_value = value.replace("'", "")
            bootstrap_entries.append(f"{safe_key}: '{safe_value}'")

    bootstrap_script = (
        "<script>"
        "(function(){"
        f"window.__ERP_BOOTSTRAP__={{{', '.join(bootstrap_entries)}}};"
        "})();"
        "</script>"
    )

    if "</body>" in html:
        html = html.replace("</body>", f"{bootstrap_script}\n</body>")
    else:
        html = f"{html}\n{bootstrap_script}"

    return HTMLResponse(
        content=html,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
