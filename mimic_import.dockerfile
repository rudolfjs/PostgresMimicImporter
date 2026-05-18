FROM ghcr.io/prefix-dev/pixi:0.67.2

LABEL Maintainer="Rudolf J"

WORKDIR /usr/src/app

# psql is shelled out by _db_handler; libpq comes with conda-forge psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Resolve deps from manifest + lock before copying source so layer caches
COPY pyproject.toml pixi.lock ./
RUN pixi install --locked -e default

COPY pgmimic/ ./pgmimic/

CMD ["pixi", "run", "-e", "default", "mimic-import"]
