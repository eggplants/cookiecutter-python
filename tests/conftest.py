from __future__ import annotations

from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _no_priming(monkeypatch):
    """Keep `git init`, `uv lock` and the PyPI lookup out of the test suite."""
    monkeypatch.setenv("COOKIECUTTER_NO_PRIME", "1")
    monkeypatch.setenv("COOKIECUTTER_NO_PYPI_CHECK", "1")


@pytest.fixture
def bake(tmp_path):
    """Generate a project from the template and hand back its root."""

    def _bake(**context):
        return Path(
            cookiecutter(
                str(TEMPLATE),
                no_input=True,
                output_dir=str(tmp_path),
                overwrite_if_exists=True,
                extra_context=context,
            ),
        )

    return _bake
