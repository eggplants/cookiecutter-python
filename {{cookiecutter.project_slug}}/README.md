# {{ cookiecutter.project_name }}

[![PyPI](
  <https://img.shields.io/pypi/v/{{ cookiecutter.project_slug }}?color=blue>
  )](
  <https://pypi.org/project/{{ cookiecutter.project_slug }}/>
) [![CI](
  <https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/actions/workflows/ci.yml/badge.svg>
  )](
  <https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/actions/workflows/ci.yml>
)
{% if cookiecutter.use_docker == "yes" and cookiecutter.project_type == "cli" %}
[![ghcr size](
  <https://ghcr-badge.egpl.dev/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/size>
)](
  <https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/pkgs/container/{{ cookiecutter.project_slug }}>
)
{% endif %}
{{ cookiecutter.project_description }}

## Installation
{% if cookiecutter.project_type == "cli" %}
```bash
{%- if cookiecutter.use_pyinstaller == "yes" %}
# mise via github, the standalone binary below
mise use -g github:{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}
{% endif %}
# mise via pipx
mise use -g pipx:{{ cookiecutter.project_slug }}

# pipx
pipx install {{ cookiecutter.project_slug }}

# pip
pip install {{ cookiecutter.project_slug }}
```
{%- else %}
```bash
# uv
uv add {{ cookiecutter.project_slug }}

# pip
pip install {{ cookiecutter.project_slug }}
```
{%- endif %}
{%- if cookiecutter.use_docker == "yes" and cookiecutter.project_type == "cli" %}

### Docker

```bash
docker pull ghcr.io/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}

docker run --rm ghcr.io/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }} eggplant
```
{%- endif %}
{% if cookiecutter.project_type == "cli" %}
## CLI

```shellsession
$ {{ cookiecutter.command_name }}
Hello, world!

$ {{ cookiecutter.command_name }} eggplant
Hello, eggplant!
```
{% endif %}
## Library

```python
import {{ cookiecutter.package_name }}

print({{ cookiecutter.package_name }}.__version__)
```

## License

[MIT License](
  <https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}/blob/master/LICENSE.txt>
)
