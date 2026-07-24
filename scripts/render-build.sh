#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip

python - <<'PY'
from pathlib import Path
import subprocess
import sys
import tomllib

data = tomllib.loads(Path("pyproject.toml").read_text())

dependencies = list(data.get("project", {}).get("dependencies", []))

if not dependencies:
    raise SystemExit("No project dependencies found in pyproject.toml")

subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    *dependencies,
])
PY