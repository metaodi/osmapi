#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# Check PEP-8 code style and McCabe complexity
flake8 --statistics --show-source .

# run tests
nosetests --verbose --with-coverage

# generate the docs
pdoc -o . osmapi

# setup a new virtualenv and try to install the lib
virtualenv pyenv
source pyenv/bin/activate && pip install .
