pip install --upgrade pip
pip install "poetry==1.1.12"
poetry config virtualenvs.create false

if [ "$1" = "--no-dev" ]; then
    poetry install --no-interaction --no-ansi --no-dev
else
    poetry install --no-interaction --no-ansi
fi
