FROM python:3.10-slim-bullseye

LABEL Maintainer="Rudolf J"

WORKDIR /usr/src/app

# COPY
# COPY config.json ./config.json
COPY requirements.txt ./requirements.txt
COPY pgmimic/ ./

## Kernel requirements

RUN apt-get update && \
    apt-get install -y zip libpq-dev python3-dev gcc postgresql-client-common postgresql-client

# Install pip requirements
RUN pip install -r requirements.txt

CMD ["python","main.py"]