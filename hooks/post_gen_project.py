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
CREATE_GITHUB_REPO = "{{ cookiecutter.create_github_repo }}" == "yes"
PACKAGE_NAME = "{{ cookiecutter.package_name }}"
GITHUB_REPO = "{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}"
PROJECT_DESCRIPTION = "{{ cookiecutter.project_description }}"

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


def create_github_repo() -> None:
    """Create the private repository, push to it and set the release rules."""
    hint = "create the repository yourself; TODO.md carries the commands"
    if not run("gh", "auth", "status"):
        note(hint)
        return
    created = run(
        "gh",
        "repo",
        "create",
        GITHUB_REPO,
        "--private",
        "--source=.",
        "--remote=origin",
        "--push",
        "--description",
        PROJECT_DESCRIPTION,
    )
    if not created:
        note(hint)
        return
    run(
        "gh",
        "repo",
        "edit",
        GITHUB_REPO,
        "--enable-merge-commit",
        "--enable-squash-merge=false",
        "--enable-rebase-merge=false",
    )
    run("gh", "api", "--silent", "-X", "PUT", f"repos/{GITHUB_REPO}/immutable-releases")


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
    # `uv lock` and `mise run pinup` first, so the lock file and the pinned
    # digests land in the initial `git add`.
    run("uv", "lock", "--quiet")
    run("mise", "run", "pinup")
    if not run("git", "init", "--initial-branch=master", "--quiet"):
        return
    if not (run("git", "add", "--all") and run("git", "commit", "--quiet", "-m", "init")):
        return
    if CREATE_GITHUB_REPO:
        create_github_repo()


if __name__ == "__main__":
    main()
