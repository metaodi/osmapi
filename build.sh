#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# Check PEP-8 code style and McCabe complexity
flake8 --statistics --show-source .

# run tests
pytest --cov=osmapi tests/

# generate the docs
pdoc -o docs osmapi

# setup a new virtualenv and try to install the lib
virtualenv pyenv
source pyenv/bin/activate && pip install .
