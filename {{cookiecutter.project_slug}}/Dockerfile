FROM python:{{ cookiecutter.__docker_python_version }}-slim AS builder

ARG VERSION
ENV VERSION=${VERSION:-master}

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
RUN /opt/venv/bin/pip install --no-cache-dir \
    "git+https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.project_slug }}@${VERSION}"

{% if cookiecutter.use_distroless == "yes" -%}
FROM al3xos/python-distroless:{{ cookiecutter.__docker_python_version }}-debian13
COPY --from=builder /opt/venv /opt/venv
# Nothing in here launches a venv, so the interpreter is called directly and told
# where the packages landed.
ENV PYTHONPATH="/opt/venv/lib/python{{ cookiecutter.__docker_python_version }}/site-packages"

ENTRYPOINT ["python", "/opt/venv/bin/{{ cookiecutter.command_name }}"]
{%- else -%}
FROM python:{{ cookiecutter.__docker_python_version }}-slim
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["{{ cookiecutter.command_name }}"]
{%- endif %}
