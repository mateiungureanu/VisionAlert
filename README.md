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
when a run finds no new or improved offers for that user.

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
