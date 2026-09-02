"""Validate the answers before anything is written to disk."""

from __future__ import annotations

import keyword
import os
import re
import sys
import urllib.error
import urllib.request
from http import HTTPStatus

SLUG_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
COMMAND_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

PYPI_SIMPLE_URL = "https://pypi.org/simple/{name}/"
PYPI_TIMEOUT_SECONDS = 5

PROJECT_SLUG = "{{ cookiecutter.project_slug }}"
PACKAGE_NAME = "{{ cookiecutter.package_name }}"
COMMAND_NAME = "{{ cookiecutter.command_name }}"
MIN_AGE = "{{ cookiecutter.min_age }}"


def fail(message: str) -> None:
    """Abort generation with a message on stderr."""
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def note(message: str) -> None:
    """Print a line the user will see, without stopping generation."""
    print(f"note: {message}", file=sys.stderr)


def pypi_name_is_taken(name: str) -> bool | None:
    """Ask the PyPI simple index about a name; None when the question could not be asked."""
    request = urllib.request.Request(PYPI_SIMPLE_URL.format(name=name), method="HEAD")  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=PYPI_TIMEOUT_SECONDS) as response:  # noqa: S310
            return response.status == HTTPStatus.OK
    except urllib.error.HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            return False
        return None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def check_pypi_name(name: str) -> None:
    """Warn when the distribution name is already published on PyPI."""
    if os.environ.get("COOKIECUTTER_NO_PYPI_CHECK"):
        return
    taken = pypi_name_is_taken(name)
    if taken is None:
        note(f"PyPI could not be reached; {name!r} was not checked")
    elif taken:
        note(
            f"{name!r} is already taken on PyPI ({PYPI_SIMPLE_URL.format(name=name)}); "
            "publishing under that name will be refused",
        )


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
    check_pypi_name(PROJECT_SLUG)


if __name__ == "__main__":
    main()
