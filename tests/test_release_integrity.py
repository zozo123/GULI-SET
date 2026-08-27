from __future__ import annotations

import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest

import gulliblebench


def test_runtime_and_package_metadata_versions_match() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["version"] == version("gulliblebench") == gulliblebench.__version__
    citation = Path("CITATION.cff").read_text(encoding="utf-8")
    assert f"version: {project['version']}\n" in citation


def test_release_manifest_is_current_and_complete() -> None:
    if not Path(".git").exists():
        pytest.skip("repository manifest requires a Git checkout")
    subprocess.run([sys.executable, "scripts/verify_manifest.py"], check=True)
