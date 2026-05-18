# Postgres MIMIC Importer

<a href="/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/MIT-purple?style=for-the-badge&label=LICENSE"></a>
<a href="https://www.python.org/downloads/"><img alt="Python Version: 3.10" src="https://img.shields.io/badge/3.10-green?style=for-the-badge&label=Python&logo=python"></a>
<a href="https://pixi.sh"><img alt="Env manager: pixi" src="https://img.shields.io/badge/pixi-yellow?style=for-the-badge&label=Env&logo=pixi"></a>
<a href="https://docs.astral.sh/ruff/"><img alt="Code style: ruff" src="https://img.shields.io/badge/ruff-black?style=for-the-badge&label=Code%20Style"></a>

****

MIMIC data importer for PostgreSQL.

This repository **does not** contain **any** `MIMIC` data.

## Data

The location of the `MIMIC` is to be set as an environment variable before running `docker-compose`.

### Data Preparation

As `MIMIC-IV` and `MIMIC-IV-ED` are separate downloads, please ensure that all data is copied into a single target folder.

The target folder must have the following structure:

```bash
.
data
└───mimiciv
    └───<version>
        ├───ed
        ├───hosp
        └───icu
```

If you do not require `MIMIC-IV-ED` data to be imported, edit the `config.json` file to remove the import.

### Set the target location

Using the environment variable (default):

#### Windows

PowerShell:
```PowerShell
$env:MIMIC_DATA_PATH = "C:/absolute/path/to/mimic/data"
```

Command Prompt:

```commandline
set MIMIC_DATA_PATH=C:/absolute/path/to/mimic/data
```

#### Linux

```Bash
export MIMIC_DATA_PATH=/absolute/path/to/mimic/data
```

The `docker-compose.yaml` can be edited to hard code the location:

```yaml
version: "3"
services:
  mimic_import:
    volumes:
       - /absolute/path/to/mimic/data/:/usr/src/app/data
```

### Compatible Data Versions

| MIMIC Dataset | Version Compatibility |
|:--------------|:----------------------|
| MIMIC-IV      | 2.0                   |
| MIMIC-IV-ED   | 2.0                   |
| MIMIC-IV      | 2.2                   |
| MIMIC-IV-ED   | 2.2                   |

## Build MIMIC-IV database services

```bash
docker-compose build
```

The service can be started and stopped after being built:

1. Start the service: `docker-compose up`
    * Start the service as a background daemon: `docker-compose up -d`
2. Stop the service: `docker-compose down`
3. Stop the service and remove data: `docker-compose down -v`

## Development

The Python environment is managed with [pixi](https://pixi.sh). The manifest lives in
`pyproject.toml` and the lockfile (`pixi.lock`) is committed for reproducibility.

```bash
# Install the default (runtime) environment
pixi install

# Run the importer locally (expects ./config.json and ./data/...)
pixi run mimic-import

# Dev tasks (available in the `dev` environment)
pixi run -e dev lint        # ruff check
pixi run -e dev format      # ruff format
pixi run -e dev test        # pytest
pixi run -e dev typecheck   # ty check
```

## License
```license
MIT License

Copyright (c) 2024 Rudolf J

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
