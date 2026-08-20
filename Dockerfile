FROM node:22-bookworm-slim AS node_runtime

FROM docker:29-cli AS docker_cli


FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app


# --------------------------------------------------
# Linux/network utilities
# --------------------------------------------------

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        iproute2 \
        procps \
        curl \
    && rm -rf /var/lib/apt/lists/*


# --------------------------------------------------
# Node.js 22 + npm/npx
# --------------------------------------------------

COPY --from=node_runtime \
    /usr/local/bin/node \
    /usr/local/bin/node

COPY --from=node_runtime \
    /usr/local/lib/node_modules \
    /usr/local/lib/node_modules

RUN ln -s \
        /usr/local/lib/node_modules/npm/bin/npm-cli.js \
        /usr/local/bin/npm && \
    ln -s \
        /usr/local/lib/node_modules/npm/bin/npx-cli.js \
        /usr/local/bin/npx


# --------------------------------------------------
# Docker CLI
# --------------------------------------------------

COPY --from=docker_cli \
    /usr/local/bin/docker \
    /usr/local/bin/docker


# --------------------------------------------------
# DBHub
# --------------------------------------------------

RUN npm install -g @bytebase/dbhub@1.2.0


# --------------------------------------------------
# Python
# --------------------------------------------------

COPY requirements.txt /app/requirements.txt

RUN pip install \
    -r /app/requirements.txt


# --------------------------------------------------
# Application
# --------------------------------------------------

COPY apps/agent /app/agent
COPY apps/api /app/api


WORKDIR /app/api


EXPOSE 8000


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
