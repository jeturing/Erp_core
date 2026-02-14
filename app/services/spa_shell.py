"""Helpers to serve the compiled SPA shell from FastAPI routes."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from fastapi.responses import HTMLResponse

BASE_DIR = Path(__file__).resolve().parents[2]
SPA_INDEX_PATH = BASE_DIR / "static" / "spa" / "index.html"


def _inject_bootstrap(html: str, script: str) -> str:
    if "</body>" in html:
        return html.replace("</body>", f"{script}\n</body>")
    return f"{html}\n{script}"


def render_spa_shell(default_route: str, globals_map: Mapping[str, str] | None = None) -> HTMLResponse:
    """
    Return the built SPA index.html with a small bootstrap script.

    - Ensures a default hash route when URL has no hash fragment.
    - Exposes optional values under `window.__ERP_BOOTSTRAP__`.
    """
    if not SPA_INDEX_PATH.exists():
        return HTMLResponse(
            content=(
                "<h1>SPA build no disponible</h1>"
                "<p>Ejecuta scripts/build_static.sh para generar static/spa.</p>"
            ),
            status_code=503,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    html = SPA_INDEX_PATH.read_text(encoding="utf-8")

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
        "if(!window.location.hash){"
        f"window.location.hash='/{default_route}';"
        "}"
        "})();"
        "</script>"
    )

    return HTMLResponse(
        content=_inject_bootstrap(html, bootstrap_script),
        headers={
            # Evita que proxies/CDN sirvan un shell HTML viejo con hashes de assets obsoletos.
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
