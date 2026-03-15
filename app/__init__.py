# Onboarding System App
# Load the environment selected by ERP_ENV before importing submodules.
import os
from pathlib import Path

from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent
_erp_env = os.getenv("ERP_ENV", "development").lower().strip()
_env_files = {
    "development": _project_root / ".env",
    "test": _project_root / ".env.test",
    "production": _project_root / ".env.production",
}
_env_file = _env_files.get(_erp_env, _project_root / ".env")

if _env_file.exists():
    load_dotenv(_env_file, override=True)
else:
    load_dotenv(_project_root / ".env", override=True)
