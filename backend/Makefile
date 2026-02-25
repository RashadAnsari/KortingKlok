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

db-migrate:
	python manage.py migrate

django-shell:
	python manage.py shell

runserver:
	python manage.py runserver

runworker:
	celery --app=baseapi worker --queues=celery,celery-slow --pool=solo --concurrency=1

up:
	docker compose up -d

down:
	docker compose down
