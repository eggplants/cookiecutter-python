from __future__ import annotations

import datetime
import re
import tomllib

import ast
from pathlib import Path

import pytest
import yaml
from cookiecutter.exceptions import FailedHookException


def parse_every_python_file(root: Path) -> None:
    """Fail if any generated .py file is not valid Python."""
    for path in root.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def parse_every_workflow(root: Path) -> dict[str, dict]:
    """Load every generated workflow, failing on invalid YAML."""
    return {
        path.name: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted((root / ".github" / "workflows").glob("*.yml"))
    }


ALWAYS_PRESENT = [
    "pyproject.toml",
    "TODO.md",
    "mise.toml",
    "README.md",
    "CLAUDE.md",
    "LICENSE.txt",
    ".gitignore",
    ".github/dependabot.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/docs.yml",
    ".github/workflows/release.yml",
]


def test_default_answers_produce_a_cli_project(bake):
    project = bake()
    assert project.name == "my-python-project"
    for relative_path in ALWAYS_PRESENT:
        assert (project / relative_path).is_file(), relative_path
    assert (project / "my_python_project" / "cli.py").is_file()
    assert (project / "my_python_project" / "__main__.py").is_file()
    assert (project / "my_python_project" / "py.typed").is_file()
    assert (project / "tests" / "test_my_python_project.py").is_file()
    parse_every_python_file(project)
    parse_every_workflow(project)


def test_names_are_derived_from_the_project_name(bake):
    project = bake(project_name="Deep Fried Eggplant")
    assert project.name == "deep-fried-eggplant"
    assert (project / "deep_fried_eggplant" / "__init__.py").is_file()

    pyproject = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["name"] == "deep-fried-eggplant"
    assert pyproject["project"]["scripts"] == {"deep-fried-eggplant": "deep_fried_eggplant.cli:main"}
    assert pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["deep_fried_eggplant"]


def test_python_version_sets_the_floor_and_the_classifiers(bake):
    pyproject = tomllib.loads((bake(python_version="3.12") / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["requires-python"] == ">=3.12"
    versions = [
        classifier.rsplit(" ", 1)[-1]
        for classifier in pyproject["project"]["classifiers"]
        if classifier.startswith("Programming Language :: Python :: 3.")
    ]
    assert versions == ["3.12", "3.13", "3.14"]


def test_library_projects_have_no_cli_docker_or_binaries(bake):
    project = bake(project_type="library", use_docker="yes", use_pyinstaller="yes")
    assert not (project / "my_python_project" / "cli.py").exists()
    assert not (project / "my_python_project" / "__main__.py").exists()
    assert not (project / "Dockerfile").exists()
    assert not (project / "packaging").exists()
    assert not (project / ".github" / "workflows" / "build-binaries.yml").exists()

    pyproject = tomllib.loads((project / "pyproject.toml").read_text(encoding="utf-8"))
    assert "scripts" not in pyproject["project"]
    parse_every_python_file(project)


@pytest.mark.parametrize("use_docker", ["yes", "no"])
def test_docker_files_follow_the_answer(bake, use_docker):
    project = bake(use_docker=use_docker)
    assert (project / "Dockerfile").is_file() is (use_docker == "yes")
    assert (project / ".dockerignore").is_file() is (use_docker == "yes")

    release = parse_every_workflow(project)["release.yml"]
    assert ("ghcr" in release["jobs"]) is (use_docker == "yes")
    if use_docker == "yes":
        assert release["jobs"]["ghcr-merge"]["needs"] == "ghcr"


def test_distroless_switches_the_runtime_base(bake):
    slim = (bake() / "Dockerfile").read_text(encoding="utf-8")
    assert "al3xos" not in slim
    assert slim.rstrip().endswith('ENTRYPOINT ["my-python-project"]')

    distroless = (bake(use_distroless="yes") / "Dockerfile").read_text(encoding="utf-8")
    match = re.search(r"FROM python:(\S+)-slim AS builder", distroless)
    assert match, "the builder stage no longer pins a python version"
    version = match.group(1)
    # Nothing launches the venv in there: the interpreter is called directly and
    # PYTHONPATH is what makes the copied site-packages importable, so both
    # stages have to agree on the interpreter version.
    assert f"FROM al3xos/python-distroless:{version}-debian13" in distroless
    assert f'ENV PYTHONPATH="/opt/venv/lib/python{version}/site-packages"' in distroless
    assert distroless.rstrip().endswith('ENTRYPOINT ["python", "/opt/venv/bin/my-python-project"]')


def test_release_creates_the_release_when_there_are_no_binaries(bake):
    release = parse_every_workflow(bake(use_pyinstaller="no"))["release.yml"]
    # PyYAML reads a bare `on:` key as the boolean True.
    assert release[True] == {"push": {"tags": ["v*.*.*"]}}
    assert release["jobs"]["release"]["permissions"]["contents"] == "write"
    assert release["jobs"]["pypi"]["needs"] == "release"


def test_binaries_take_over_creating_the_release(bake):
    project = bake(use_pyinstaller="yes")
    assert (project / "packaging" / "entrypoint.py").is_file()
    assert (project / "packaging" / "my-python-project.spec").is_file()
    parse_every_python_file(project)

    workflows = parse_every_workflow(project)
    assert workflows["release.yml"][True] == {"release": {"types": ["published"]}}
    assert "release" not in workflows["release.yml"]["jobs"]
    assert "needs" not in workflows["release.yml"]["jobs"]["pypi"]

    binaries = workflows["build-binaries.yml"]
    assert binaries["jobs"]["release"]["needs"] == "build"
    assert len(binaries["jobs"]["build"]["strategy"]["matrix"]["include"]) == 6


@pytest.mark.parametrize("project_name", ["Apple Pie", "Test Hoge", "Zebra Tool"])
def test_per_file_ignores_come_out_sorted(bake, project_name):
    # pyproject-fmt sorts these globs, so an unsorted template fails `mise run ci`
    # in the generated project -- and where the package glob lands among the fixed
    # ones depends on the package name.
    pyproject = tomllib.loads(
        (bake(project_name=project_name, use_pyinstaller="yes") / "pyproject.toml").read_text(encoding="utf-8"),
    )
    globs = list(pyproject["tool"]["ruff"]["lint"]["per-file-ignores"])
    assert globs == sorted(globs)
    assert len(globs) == 3


def test_todo_lists_the_setup_that_needs_a_human(bake):
    todo = (bake(project_name="Bin Proj", use_pyinstaller="yes") / "TODO.md").read_text(encoding="utf-8")
    assert todo.count("- [ ] ") == 4
    assert "- [x]" not in todo
    assert "gh repo edit eggplants/bin-proj" in todo
    assert "gh api -X POST '/repos/eggplants/bin-proj/pages'" in todo
    assert "oidc-in-pypi" in todo
    assert "build-binaries.yml" in todo


def test_github_expressions_survive_rendering(bake):
    ci = (bake() / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "${{ github.workflow }}-${{ github.ref }}" in ci


def test_the_license_year_defaults_to_this_year(bake):
    this_year = str(datetime.datetime.now(tz=datetime.timezone.utc).year)
    assert f"Copyright (c) {this_year} eggplants" in (bake() / "LICENSE.txt").read_text(encoding="utf-8")


def test_the_license_year_can_be_answered(bake):
    project = bake(year="2020", author_name="Haruna")
    assert "Copyright (c) 2020 Haruna" in (project / "LICENSE.txt").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("field", "value"),
    [("project_name", "Bad Name!"), ("package_name", "class"), ("package_name", "9lives")],
)
def test_invalid_names_are_refused(bake, field, value):
    with pytest.raises(FailedHookException):
        bake(**{field: value})


@pytest.mark.parametrize(
    ("project_type", "sections"),
    [("cli", ["Installation", "CLI", "Library", "License"]), ("library", ["Installation", "Library", "License"])],
)
def test_the_readme_keeps_its_shape(bake, project_type, sections):
    readme = (bake(project_type=project_type) / "README.md").read_text(encoding="utf-8").splitlines()
    assert readme[0] == "# My Python Project"
    assert [line.removeprefix("## ") for line in readme if line.startswith("## ")] == sections


def test_install_matches_what_the_project_ships(bake):
    cli = (bake() / "README.md").read_text(encoding="utf-8")
    assert "pipx install my-python-project" in cli
    assert "docker pull ghcr.io/eggplants/my-python-project" in cli
    # The `github` backend pulls release assets, which only exist with binaries.
    assert "mise use -g github:" not in cli

    binaries = (bake(use_pyinstaller="yes") / "README.md").read_text(encoding="utf-8")
    assert "mise use -g github:eggplants/my-python-project" in binaries

    library = (bake(project_type="library", use_docker="yes") / "README.md").read_text(encoding="utf-8")
    assert "uv add my-python-project" in library
    assert "pipx" not in library
    assert "docker" not in library


def test_ci_only_installs_the_tools_it_needs(bake):
    project = bake(use_pyinstaller="yes")
    marked = [
        line for line in (project / "mise.toml").read_text(encoding="utf-8").splitlines() if "# [skip ci]" in line
    ]
    assert marked, "no tool is marked local-only"

    for path in sorted((project / ".github" / "workflows").glob("*.yml")):
        body = path.read_text(encoding="utf-8")
        if "jdx/mise-action" not in body:
            continue
        assert r"sed -i '/# \[skip ci\]/d' mise.toml" in body, path.name
        assert body.index("sed -i") < body.index("jdx/mise-action"), path.name
