#!/bin/bash

[ ! -d pyenv ] && python -m venv pyenv
source pyenv/bin/activate

make deps
pip install -e .
