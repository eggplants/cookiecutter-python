"""Bump the dependency versions written into the template.

The template tree is Jinja, so uv cannot read its pyproject.toml directly: a
project is baked into a scratch directory, `uv sync -U` runs there, and the
locked versions are written back as the lower bounds in the template. The
workflows and the Dockerfile are line-based enough for pinact and
dockerfile-pin to update in place.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from cookiecutter.main import cookiecutter

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "{{cookiecutter.project_slug}}"
TEMPLATE_PYPROJECT = TEMPLATE_DIR / "pyproject.toml"
# Every optional file switched on, so nothing the template can emit is missed.
BAKE_CONTEXT = {"project_type": "cli", "use_docker": "yes", "use_pyinstaller": "yes"}
LOWER_BOUND = re.compile(r'"(?P<name>[A-Za-z0-9._-]+)>=(?P<version>[0-9][0-9.]*)"')


def normalize(name: str) -> str:
    """Normalize a distribution name as PEP 503 does."""
    return re.sub(r"[-_.]+", "-", name).lower()


def run(*command: str, cwd: Path) -> None:
    """Run a command and stop on the first failure."""
    print(f"$ {' '.join(command)}", file=sys.stderr)
    subprocess.run(command, check=True, cwd=cwd)  # noqa: S603


def locked_versions() -> dict[str, str]:
    """Bake a project, upgrade its lock and return the locked versions."""
    os.environ["COOKIECUTTER_NO_PRIME"] = "1"
    os.environ["COOKIECUTTER_NO_PYPI_CHECK"] = "1"
    with tempfile.TemporaryDirectory() as tmp:
        baked = Path(
            cookiecutter(str(ROOT), no_input=True, output_dir=tmp, extra_context=BAKE_CONTEXT),
        )
        run("uv", "sync", "-U", cwd=baked)
        lock = tomllib.loads((baked / "uv.lock").read_text(encoding="utf-8"))
    return {normalize(package["name"]): package["version"] for package in lock["package"] if "version" in package}


def release(version: str) -> tuple[int, ...]:
    """Return the numeric release segment of a version string."""
    return tuple(int(part) for part in re.findall(r"\d+", version.split("+", maxsplit=1)[0])[:3])


def bump_lower_bounds(versions: dict[str, str]) -> None:
    """Raise each `name>=x` in the template to the locked version.

    A bound keeps as many components as it had (`pdoc>=16` stays a major-only
    bound), and is never lowered.
    """

    def replace(match: re.Match[str]) -> str:
        name, current = match["name"], match["version"]
        locked = versions.get(normalize(name))
        if locked is None:
            return match[0]
        width = len(current.split("."))
        candidate = ".".join(str(part) for part in release(locked)[:width])
        if release(candidate) <= release(current):
            return match[0]
        print(f"{name}: >={current} -> >={candidate}", file=sys.stderr)
        return f'"{name}>={candidate}"'

    text = TEMPLATE_PYPROJECT.read_text(encoding="utf-8")
    TEMPLATE_PYPROJECT.write_text(LOWER_BOUND.sub(replace, text), encoding="utf-8")


def main() -> None:
    """Update the Python bounds, the pinned actions and the image digests."""
    min_age = json.loads((ROOT / "cookiecutter.json").read_text(encoding="utf-8"))["min_age"]
    bump_lower_bounds(locked_versions())
    run("pinact", "run", "-u", "--min-age", min_age, cwd=TEMPLATE_DIR)
    run("dockerfile-pin", "run", "-u", "--write", "--min-age", min_age, "-f", "Dockerfile", cwd=TEMPLATE_DIR)


if __name__ == "__main__":
    main()
