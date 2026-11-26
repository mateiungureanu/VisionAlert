# VisionAlert

## Development

Pull the latest changes and apply migrations from the repository root:

```powershell
git pull
.\venv\Scripts\python.exe manage.py migrate
```

Run the backend and frontend in two terminals.

Terminal 1, from the repository root:

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

Open the frontend at `http://localhost:5173`.

After signing in, the home page (`/`) greets the user, shows how many active
offers come from the brands they follow, and lists offers from their favorite
brands. The favorites feed is paginated (12 offers per page) and can be
narrowed with the "Branduri" dropdown (multi-select with search) and with a
search box that matches words in the offer title (not the description), and
with a "Reducere" dropdown. Its options are discount bands (below 10%, 10–19%,
..., 50% or more, plus "Fără reducere specificată") built from the offers that
currently exist, each with its offer count. If no
brand is marked as favorite, the page links to the followed-brands page.

The followed-brands page (`/brands`, previously the home page) shows one card
per subscribed brand with its active offer count. The star on each card marks
the brand as a favorite; this is stored as `is_favorite` on the brand
subscription. The dropdown above the cards shows only the selected brands.
Select a brand to open its offer page, where
offers can be narrowed, on a single row, with a category dropdown (shown only
when the brand has categories), the same discount-band dropdown as the home
feed (shown only when at least one offer has a discount) and a title search
(diacritics-insensitive). Offers are grouped by category with a count for each
group. When more than one category is shown, each section can
be collapsed or expanded individually, or all at once. An offer associated
with multiple categories appears in each relevant group. Selecting categories
filters offers to those categories; offers without a category remain visible
because some scrapers cannot classify every offer. Subscriptions without
selected categories show all offers from that brand.
When the source explicitly provides them, offer cards also show the discount
percentage, previous price, and current price. Prices are stored as RON amounts;
offers without extractable price details keep those fields empty.

### Favorite offers

Users can save individual offers with the heart on an offer card (or in its
details dialog). Saved offers are listed on the "Oferte favorite" page
(`/favorite-offers`), newest saved first, with a brand dropdown, a discount-band
dropdown and a title search; the list is paginated (12 per page). Saved offers
stay listed after they expire (flagged "Expirată") and even if the user is not
subscribed to the brand, until the user removes them. This is separate from
favorite *brands* (the star on `/brands`).

They are stored in the `FavoriteOffer` association table (`user`, `offer`,
`created_at`, unique per user and offer), so a user can favorite many offers and
an offer can be favorited by many users.

- `PUT /api/favorite-offers/<offer_id>/` saves an offer, `DELETE` removes it
  (both idempotent).
- `GET /api/favorite-offers/` returns the user's saved offers (paginated;
  `brands`, `search`, `discounts` as for `/api/offers/favorites/`).
- `GET /api/favorite-offers/brands/` and `GET /api/favorite-offers/discounts/`
  return the brands and discount bands present among the saved offers, with
  counts, to build the filter dropdowns.
- Offers returned by the offer endpoints include `is_favorite`, so cards show
  the right heart state.

### Favorites API

- `PATCH /api/subscriptions/<brand_id>/favorite/` with `{"is_favorite": true}`
  marks or unmarks a subscribed brand as favorite.
- `GET /api/offers/favorites/` returns the paginated active offers of favorite
  brands. Optional query parameters: `page`, `brands=1,3` (brand ids) and
  `search=text` (case-insensitive match on the offer title) and
  `discounts=10,50,none` (discount band starts; `0` is below 10%, `50` is 50% or
  more, `none` is offers without a discount).
- `GET /api/offers/favorites/discounts/` returns the discount bands that exist,
  as `[{"key": "10", "count": 2}, ...]`. It honors `brands` and `search`, but not
  `discounts`.

## Offer email summaries

The scraping pipeline sends one summary email to each active user who is
subscribed to a brand with a newly detected or improved offer. A lower current
price or a higher discount percentage counts as an improvement. The summary
groups counts by brand and category (including uncategorized offers); a new
offer is included even when it has no comparable price data. No email is sent
when a run finds no new or improved offers for that user. For now, a brand
subscription receives alerts regardless of its selected categories; personal
offer filters are not applied.

Email delivery uses Django's console backend by default, so messages appear in
the terminal during development. The `scrape_offers` command explicitly uses
the console backend unless asked otherwise:

```powershell
.\.venv\Scripts\python.exe manage.py scrape_offers
```

For SMTP delivery, configure these values in `.env` and run the command with
`--email-backend configured`:

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=VisionAlert <alerts@example.com>
```

Keep actual SMTP credentials out of source control. Failed sends are logged;
automatic retry is not configured.

### Monitored resources

Staff can add and manage website and API resources in Django admin under
"Monitored resources". Each resource has a URL, optional brand association,
enable/disable switch, JSON parameters, optional API-key authentication, and
health status. Health checks currently consume the optional
`health_check_params` object; resource-specific offer scrapers can consume
other parameters when added. API keys are encrypted before being stored in the
database. Generate a Fernet key with:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Put the generated value in `.env` and in the secret configuration for every
web and scheduler process:

```text
RESOURCE_CREDENTIAL_ENCRYPTION_KEY=<generated-fernet-key>
```

Keep this key outside source control and back it up securely. It must remain
stable: changing or losing it without re-encrypting stored credentials makes
those credentials unreadable. In admin, leave the API-key input blank to keep
the current key, or select "Remove stored API key" to delete it. For API
authentication, use an HTTP header when supported (for example, name
`X-API-Key` with an empty prefix, or `Authorization` with the default `Bearer `
prefix). Choose query-parameter authentication only when the API requires it;
query credentials may be exposed by URL logging. Health-check parameters may
include a `health_check_params` JSON object.

Run resource checks with:

```powershell
python manage.py check_resources
```

The command makes a bounded HTTP GET for each enabled resource and stores its
last check time, health status, and error in admin. It emails active Django
staff users when a resource first fails and again when it recovers; repeated
failures do not generate duplicate alerts. The project does not configure a
scheduler, so configure the deployment's cron/scheduler to run
`manage.py check_resources` hourly, separately from `manage.py scrape_offers`.
API resources are currently monitored for availability; fetching offers from
an API such as Steam requires a resource-specific offer scraper and is not
included in this implementation.

### GitHub Actions schedule

`.github/workflows/resource-health.yml` runs `manage.py check_resources` hourly
at minute 17 UTC to avoid the busiest top-of-hour scheduling window, and also
supports manual runs from the Actions tab. Scheduled workflows run from the
default branch and GitHub may delay scheduled starts.
Before merging/enabling it, add these repository Actions secrets under
**Settings > Secrets and variables > Actions**:

- `DATABASE_URL`: the database URL, reachable from GitHub-hosted runners.
- `SECRET_KEY`: the Django secret key.
- `RESOURCE_CREDENTIAL_ENCRYPTION_KEY`: the same stable Fernet key used by the
  Django app.
- `EMAIL_HOST`, `EMAIL_PORT`, and `DEFAULT_FROM_EMAIL`: SMTP settings.
- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` if the SMTP server requires
  authentication.
- `EMAIL_USE_TLS` and `EMAIL_USE_SSL` only if you need to override the
  workflow defaults (`true` and `false` respectively).

The workflow checks that database migrations are already applied; it does not
run migrations. It only monitors resources and does not run `scrape_offers`.
Scheduling offer scraping separately requires a runner that can reach the
configured database and the scrapers' dependencies; the current Cinema City
and KFC scrapers also require the configured LM Studio service.

## Local offer extraction with LM Studio

Cinema City detail-page extraction uses the local OpenAI-compatible LM Studio
server. Load the Qwen3.5-9B model in LM Studio and start its server, then set
these values in the repository `.env` file:

```text
LM_STUDIO_BASE_URL=http://localhost:1235/v1
LM_STUDIO_MODEL=qwen3.5-9b
```

`LM_STUDIO_MODEL` must match the model identifier shown by the LM Studio server.
The Cinema City scraper sends offer-page text to this configured local server.
The KFC scraper also sends each offer image, together with the text from its
offer card and any KFC detail page or modal. KFC pages require Chromium through
Playwright; install it after installing the Python requirements:

```powershell
.\venv\Scripts\python.exe -m playwright install chromium
```

## Checks and tests

The `scrape_offers` management command prints timestamped progress for each
brand, offer extraction, and database save step.
Intersport offers are collected from the enabled categories whose URLs are
stored on their category records; each category's product pages are paginated
and offer prices and discounts are stored when shown by the product card.

From the repository root:

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test core_app
```

From the `frontend` directory:

```powershell
npm run lint
npm run build
```
