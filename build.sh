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

# generate docs (currently it's not possible to generate docs in Python 2.6)
if [[ $TRAVIS_PYTHON_VERSION != 2.6 ]]; then
    pdoc --html --overwrite osmapi/OsmApi.py
fi
