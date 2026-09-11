# Contributing to KortingKlok

Thanks for taking the time to contribute. This guide covers how to get the
project running, what the review bar is, and how to add support for a new
supermarket.

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Fix a broken scraper.** Supermarkets change their sites without warning, so
  this is where help is needed most often.
- **Add a supermarket.** See [Adding a supermarket](#adding-a-supermarket).
- **Improve the app.** Flutter screens, accessibility, dark mode, translations.
- **Report a bug.** Include the supermarket, the endpoint or screen, and what
  you expected instead.

## Getting set up

Follow [backend/README.md](backend/README.md) and [mobile/README.md](mobile/README.md).
Both parts can be worked on independently: the app talks to any backend you
point it at, and the backend runs without the app.

Enable the shared pre-commit hooks once per clone:

```bash
git config core.hooksPath .githooks
```

The hook runs `make local` in both `backend/` and `mobile/`, which formats the
code, refreshes translations, and fails the commit if linting does not pass.

## Before you open a pull request

1. `cd backend && make lint && make test`
2. `cd mobile && make lint && flutter test`
3. Keep the change focused. One concern per pull request reviews far faster.
4. Match the style of the code around you. The linters settle the rest.
5. Describe what changed and why. For a scraper fix, say what the supermarket
   changed on their side.

New user-facing strings belong in `mobile/lib/l10n/translations.dart` in both
Dutch and English, and in `backend/baseapi/local/` for anything the backend
sends out. Never hardcode visible text.

## Adding a supermarket

Scrapers only fetch and parse. Persistence, price-change detection, and
notifications are handled for you once the data comes back in the right shape.

1. Register the store in `SUPERMARKETS` in `backend/apps/products/apps.py`.
2. Create `backend/apps/products/scrapers/impls/<slug>.py`:

   ```python
   from products.scrapers.base import BaseSupermarketScraper
   from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
   from products.scrapers.registry import register_scraper


   @register_scraper
   class MyStoreScraper(BaseSupermarketScraper):
       supermarket_slug = "mystore"

       def scrape_categories(self) -> list[ScrapedCategory]:
           ...

       def scrape_products(self) -> list[ScrapedProduct]:
           ...
   ```

3. Import the module in
   `backend/apps/products/management/commands/scrape_all_supermarkets.py` so the
   decorator runs.
4. Add compatibility tests to `backend/apps/products/scrapers/impls/tests.py`.

The scraper tests are deliberately live: each one fetches a real page and
asserts a structural assumption the parser depends on, with a failure message
naming what the store must have changed. That is how a broken scraper gets
noticed, and why the backend workflow also runs on a daily schedule. Keep new
tests in the same shape: few requests, one assumption each, useful message.

Both methods return a full snapshot: products missing from `scrape_products()`
are marked unavailable on the next run. Prices are `Decimal`, never `float`.
Set `category_external_id` on each product so it links to the category you
returned from `scrape_categories()`.

### Scrape politely

A scraper that hammers a store gets the whole project blocked. Keep request
rates conservative, reuse a session, honour the site's terms, and put slow
scrapers on the `celery-slow` queue.

## Commit messages

Write a short imperative subject line that says what changed, for example
`Fix Jumbo category pagination`. The body is for why, if it is not obvious.

## License

By contributing you agree that your work is licensed under the
[MIT License](LICENSE) that covers this project.
