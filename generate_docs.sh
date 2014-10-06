#!/bin/bash

set -e

function cleanup {
    exit $?
}

trap "cleanup" EXIT

# generate docs
pdoc --html --overwrite osmapi/OsmApi.py
