#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# Check PEP-8 code style and McCabe complexity
make lint

# run tests
make test

# generate the docs
make docs

# build the package and make sure it can be installed on its own
make build
uv run --no-project --isolated --with "$(ls dist/*.whl)" \
    python -c "import osmapi; print(osmapi.__version__)"
