"""Validate the answers before anything is written to disk."""

from __future__ import annotations

import keyword
import re
import sys

SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
COMMAND_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

PROJECT_SLUG = "{{ cookiecutter.project_slug }}"
PACKAGE_NAME = "{{ cookiecutter.package_name }}"
COMMAND_NAME = "{{ cookiecutter.command_name }}"
MIN_AGE = "{{ cookiecutter.min_age }}"


def fail(message: str) -> None:
    """Abort generation with a message on stderr."""
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    """Check every name the generated project depends on."""
    if not SLUG_RE.match(PROJECT_SLUG):
        fail(
            f"project_slug {PROJECT_SLUG!r} is not a valid PyPI/repository name "
            "(lowercase letters, digits and inner hyphens only)",
        )
    if not PACKAGE_NAME.isidentifier() or keyword.iskeyword(PACKAGE_NAME):
        fail(f"package_name {PACKAGE_NAME!r} is not a valid Python module name")
    if PACKAGE_NAME != PACKAGE_NAME.lower():
        fail(f"package_name {PACKAGE_NAME!r} must be lowercase")
    if not COMMAND_RE.match(COMMAND_NAME):
        fail(f"command_name {COMMAND_NAME!r} is not a valid console script name")
    if not MIN_AGE.isdigit():
        fail(f"min_age {MIN_AGE!r} is not a whole number of days")


if __name__ == "__main__":
    main()
