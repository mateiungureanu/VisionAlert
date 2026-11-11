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

After signing in, the home page shows the total number of active offers and
groups them by subscribed brand. Select a brand to open its offer page, where
offers are grouped by category with a count for each group. An offer associated
with multiple categories appears in each relevant group. Selecting categories
filters offers to those categories; offers without a category remain visible
because some scrapers cannot classify every offer. Subscriptions without
selected categories show all offers from that brand.
When the source explicitly provides them, offer cards also show the discount
percentage, previous price, and current price. Prices are stored as RON amounts;
offers without extractable price details keep those fields empty.

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
