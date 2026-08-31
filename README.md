# cookiecutter-python

[![CI](
  <https://github.com/eggplants/cookiecutter-python/actions/workflows/ci.yml/badge.svg>
  )](
  <https://github.com/eggplants/cookiecutter-python/actions/workflows/ci.yml>
)

A [Cookiecutter](https://cookiecutter.readthedocs.io/) template for eggplants' Python projects.

## Usage

```bash
# uvx
uvx cookiecutter gh:eggplants/cookiecutter-python -o path/to/dir

# mise
mise use -g cookiecutter
cookiecutter gh:eggplants/cookiecutter-python -o path/to/dir
```

## Prompts

| [Prompt](https://cookiecutter.readthedocs.io/en/stable/tutorials/tutorial1.html#cookiecutter-json) | Default | [`__prompts__`](https://cookiecutter.readthedocs.io/en/stable/advanced/human_readable_prompts.html#) |
| --- | --- | --- |
| `project_name` | `My Python Project` | Human-readable title, used in the README heading |
| `project_slug` | derived | PyPI and repository name, e.g. `my-python-project` |
| `package_name` | derived | Importable module, e.g. `my_python_project` |
| `command_name` | derived | Console script name, CLI projects only |
| `project_description` | `A Python project.` | One line, reused in the README and the `--help` text |
| `author_name` | `eggplants` | |
| `author_email` | | |
| `github_username` | `eggplants` | Owner in the repository, badge and image URLs |
| `year` | the current year | Copyright year in `LICENSE.txt` |
| `python_version` | `3.11` | The floor; classifiers are emitted up to 3.14 |
| `project_type` | `cli` | `cli` adds `cli.py`, `__main__.py` and a console script; `library` does not |
| `use_docker` | `yes` | `Dockerfile` plus the multi-arch GHCR jobs in `release.yml` |
| `use_distroless` | `no` | Runs the image on a distroless base instead of `python:*-slim` |
| `use_pyinstaller` | `no` | `packaging/` plus `build-binaries.yml` for standalone binaries |
| `min_age` | `7` | Days a release must age before it is used: `mise` installs, Dependabot cooldowns and `mise run pinup` |
| `create_github_repo` | `no` | `yes` makes the post-generation hook `gh repo create` the private repository, push the first commit, restrict merges to merge commits and turn immutable releases on |

## License

[MIT License](<https://github.com/eggplants/cookiecutter-python/blob/master/LICENSE.txt>)
