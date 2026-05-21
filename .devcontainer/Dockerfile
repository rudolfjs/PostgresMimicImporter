FROM ghcr.io/prefix-dev/pixi:0.67.2

# psql is shelled out by _db_handler; libpq comes via conda-forge psycopg2 in the
# pixi env, but we also need the psql/gzip client binaries for the import path.
# git is added for the VS Code source-control integration.
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client gzip git && \
    rm -rf /var/lib/apt/lists/*
