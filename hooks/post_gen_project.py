"""Prune the files the chosen options do not need, then prime the project."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_TYPE = "{{ cookiecutter.project_type }}"
USE_DOCKER = "{{ cookiecutter.use_docker }}" == "yes"
USE_PYINSTALLER = "{{ cookiecutter.use_pyinstaller }}" == "yes"
USE_DISTROLESS = "{{ cookiecutter.use_distroless }}" == "yes"
PACKAGE_NAME = "{{ cookiecutter.package_name }}"

ROOT = Path.cwd()

CLI_ONLY = (
    f"{PACKAGE_NAME}/cli.py",
    f"{PACKAGE_NAME}/__main__.py",
)
DOCKER_ONLY = (
    "Dockerfile",
    ".dockerignore",
)
PYINSTALLER_ONLY = (
    "packaging",
    ".github/workflows/build-binaries.yml",
)


def note(message: str) -> None:
    """Print a line the user will see right after generation."""
    print(f"note: {message}", file=sys.stderr)


def remove(*relative_paths: str) -> None:
    """Delete files or directories that this configuration does not use."""
    for relative_path in relative_paths:
        path = ROOT / relative_path
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def run(*command: str) -> bool:
    """Run a command, reporting failure instead of aborting generation."""
    if shutil.which(command[0]) is None:
        note(f"{command[0]} is not installed; skipped `{' '.join(command)}`")
        return False
    result = subprocess.run(command, check=False, cwd=ROOT)  # noqa: S603
    if result.returncode != 0:
        note(f"`{' '.join(command)}` failed; run it yourself once the project is ready")
        return False
    return True


def main() -> None:
    """Prune and prime the freshly generated project."""
    library = PROJECT_TYPE == "library"
    if library:
        remove(*CLI_ONLY)

    docker = USE_DOCKER and not library
    if USE_DOCKER and library:
        note("use_docker was ignored: a library without a console script has nothing to run")
    if not docker:
        remove(*DOCKER_ONLY)
    if USE_DISTROLESS and not docker:
        note("use_distroless was ignored: there is no image to build it into")

    pyinstaller = USE_PYINSTALLER and not library
    if USE_PYINSTALLER and library:
        note("use_pyinstaller was ignored: there is no console script to freeze")
    if not pyinstaller:
        remove(*PYINSTALLER_ONLY)

    # The template's own test suite bakes dozens of projects; priming each one
    # would spend far longer in git and the network than in the assertions.
    if os.environ.get("COOKIECUTTER_NO_PRIME"):
        return
    # `uv lock` first, so the lock file lands in the initial `git add`.
    run("uv", "lock", "--quiet")
    if run("git", "init", "--initial-branch=master", "--quiet"):
        run("git", "add", "--all")


if __name__ == "__main__":
    main()
