local: dependencies-lock translations code-format lint

dependencies-lock:
	poetry lock --no-update

translations:
	python manage.py makemessages -l en -l nl
	python manage.py compilemessages -l en -l nl

code-format:
	ruff format
	ruff check --fix

lint:
	ruff check

test:
	pytest

db-makemigrations:
	find . -path "*/migrations/*.py" -not -name "__init__.py" -not -path "*/.venv/*" -delete # FIXME: Remove this after first release.
	python manage.py makemigrations

db-migrate:
	python manage.py migrate

db-shell:
	python manage.py dbshell

django-shell:
	python manage.py shell_plus

runserver:
	python manage.py runserver

gunicorn:
	gunicorn --config gunicorn.conf.py

celery:
	celery --app=baseapi --quiet worker --queues=main-queue

up:
	docker compose up -d

down:
	docker compose down
