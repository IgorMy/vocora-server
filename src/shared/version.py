import tomllib
from pathlib import Path

from pydantic import BaseModel

# pyproject.toml is the single source of the version (bump it with `uv version --bump ...`).
# It is read directly because, with `package = false`, the project is not installed
# and importlib.metadata has no version for it.
_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


class _Project(BaseModel):
    version: str


class _Pyproject(BaseModel):
    project: _Project


def read_version() -> str:
    with _PYPROJECT.open("rb") as f:
        return _Pyproject.model_validate(tomllib.load(f)).project.version


VERSION = read_version()

# URL prefix from the major version (0.1.0 -> /v0): it only changes on breaking releases
API_PREFIX = f"/v{VERSION.split('.')[0]}"

# API docs live under the versioned prefix too, next to the endpoints they describe
DOCS_URL = f"{API_PREFIX}/docs"
OPENAPI_URL = f"{API_PREFIX}/openapi.json"
