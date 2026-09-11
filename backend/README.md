# KortingKlok backend

Django REST API and Celery workers that scrape Dutch supermarkets, store price
history, and push notifications when a followed product changes price.

## Requirements

- Python 3.13
- Docker, for the local Postgres and Redis
- A Firebase project, for authentication and push notifications

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install poetry==1.8.5
poetry config virtualenvs.create false
poetry install
```

Copy the environment template and fill it in:

```bash
cp .env.example .env
```

Download a service account key from your Firebase project (Project settings >
Service accounts > Generate new private key), save it as
`backend/firebase-adminsdk.json`, and point `GOOGLE_APPLICATION_CREDENTIALS`
at it. The file is gitignored.

## Running

Start Postgres and Redis, then migrate:

```bash
make up
make db-migrate
```

Run the API on `http://localhost:8000`:

```bash
make runserver
```

Run a worker in a second terminal, so scrape and notification tasks execute:

```bash
make runworker
```

Kick off a scrape of every registered supermarket:

```bash
python manage.py scrape_all_supermarkets
```

The task dispatches one job per supermarket. Lidl goes to the `celery-slow`
queue because a full run takes considerably longer than the others.

Send yourself a push notification to verify Firebase is wired up:

```bash
python manage.py send_test_notification <firebase-uid>
```

Stop the containers with `make down`.

## Quality

```bash
make format   # ruff format and autofix
make lint     # ruff check
make test     # pytest
make local    # lock, translations, format, lint (what the pre-commit hook runs)
```

The scraper tests fetch real supermarket pages and assert the structure each
parser relies on, so a failure there usually means a store changed their site
rather than that the code regressed. The workflow runs daily for that reason.

## API

All routes are versioned under `/v1` and authenticated with a Firebase ID token
sent as `Authorization: Bearer <token>`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/v1/health` | Liveness check |
| GET | `/v1/products/supermarkets` | List supported supermarkets |
| GET | `/v1/products/categories` | List categories, filtered per supermarket |
| GET | `/v1/products/search` | Search products |
| GET | `/v1/products/deals` | Products currently discounted |
| POST / DELETE | `/v1/products/<id>/track` | Follow or unfollow a product |
| POST | `/v1/users/devices` | Register a device for push notifications |
| POST | `/v1/users/logout` | Unregister the current device |

## Layout

```
apps/
  apis/      versioned routing, error formatting, throttling
  products/  models, endpoints, scrapers, notifications
    scrapers/
      base.py      BaseSupermarketScraper interface
      dtos.py      ScrapedProduct and ScrapedCategory
      registry.py  @register_scraper and lookup by slug
      persists.py  snapshot sync and price-change detection
      impls/       one module per supermarket
  users/     Firebase token auth, devices, tracked products
  utils/     shared model mixins and Celery retry base
baseapi/     settings, Celery app, URLs, translations
```

Scrapers return a full snapshot on every run. `persists.py` diffs that snapshot
against the database, marks missing products unavailable, records price changes
against a run id, and hands the changed set to the notification tasks.

Adding a supermarket is described in [../CONTRIBUTING.md](../CONTRIBUTING.md).
