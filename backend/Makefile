local: dependencies-lock translations format lint

dependencies-lock:
	poetry lock --no-update

translations:
	python manage.py makemessages -l en -l nl
	python manage.py compilemessages -l en -l nl

format:
	ruff format
	ruff check --fix

lint:
	ruff check

test:
	pytest

db-makemigrations:
	python manage.py makemigrations

db-migrate:
	python manage.py migrate

django-shell:
	python manage.py shell

local-server:
	python manage.py runserver

local-worker:
	celery --app=baseapi worker --queues=default --pool=solo

prod-server:
	gunicorn --config gunicorn.conf.py

prod-worker:
	celery --app=baseapi worker --queues=default

scrape-all-supermarkets:
	python manage.py scrape_all_supermarkets

up:
	docker compose up -d

down:
	docker compose down
