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

# setup a new virtualenv and try to install the lib
virtualenv pyenv
source pyenv/bin/activate && pip install .
