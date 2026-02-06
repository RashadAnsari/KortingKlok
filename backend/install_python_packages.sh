#!/bin/sh

pip install --upgrade pip
pip install "poetry==1.8.5"
poetry config virtualenvs.create false

if [ "$1" = "--no-dev" ]; then
    poetry install --no-interaction --no-ansi --without dev
else
    poetry install --no-interaction --no-ansi
fi
