from __future__ import annotations

import re
import unicodedata
import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Iterable
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import sync_playwright

from core_app.scraping.contracts import ScrapedOffer

if TYPE_CHECKING:
    from playwright.sync_api import Page

OFFERS_URL = (
    "https://comenzi.farmaciatei.ro/eveniment/"
    "zorii-reducerilor-volumul-x-november-2026"
)
FARMACIA_TEI_DOMAIN = "farmaciatei.ro"
REQUEST_TIMEOUT_MS = 30_000
logger = logging.getLogger(__name__)

_OFFER_PATTERNS = (
    ("Reducere pana la", r"\bpana\s+la\s+\d+\s*%(?:\s+reducere)?"),
    ("Reducere procentuala", r"\b\d+\s*%(?:\s+reducere)?"),
    ("Multi-buy", r"\b\d+\s+la\s+pret\s+de\s+\d+\b"),
    ("Multi-buy", r"\bcumperi\s+\d+\s*,?\s*platesti\s+\d+\b"),
    ("Pachet promotional", r"\bpachete?\s+avantajoase?\b"),
)


def scrape_farmacia_tei_offers(url: str = OFFERS_URL) -> list[ScrapedOffer]:
    if not _is_farmacia_tei_url(url):
        raise ValueError("Farmacia Tei offers URL must use the farmaciatei.ro domain")

    category_names = _load_category_names()
    if not category_names:
        raise ValueError("No enabled Farmacia Tei categories were found in the database")
    logger.info(
        "Farmacia Tei: scraping %d enabled categories",
        len(category_names),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(locale="ro-RO")
            page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT_MS)
            _dismiss_cookie_banner(page)
            page.wait_for_selector(
                "button.btn-outline-primary", timeout=REQUEST_TIMEOUT_MS
            )

            option_labels = page.locator("button.btn-outline-primary").evaluate_all(
                "buttons => buttons.map(button => button.innerText.trim())"
            )
            matching_options = _match_category_options(category_names, option_labels)
            if not matching_options:
                raise ValueError(
                    "No enabled Farmacia Tei database categories match the "
                    "categories on the offers page"
                )
            logger.info(
                "Farmacia Tei: matched %d database categories to the offers page",
                len(matching_options),
            )

            offers_by_url: dict[str, ScrapedOffer] = {}
            for index, (category_name, option_label) in enumerate(
                matching_options, start=1
            ):
                logger.info(
                    "Farmacia Tei: scraping category %d/%d",
                    index,
                    len(matching_options),
                )
                button = page.locator("button.btn-outline-primary").filter(
                    has_text=re.compile(re.escape(option_label), re.IGNORECASE)
                )
                if button.count() != 1:
                    raise ValueError(
                        f"Expected one Farmacia Tei option for {option_label!r}, "
                        f"found {button.count()}"
                    )
                previous_hrefs = page.locator("a.campaign-banner").evaluate_all(
                    "banners => banners.map(banner => banner.href)"
                )
                button.click()
                _wait_for_category_change(page, previous_hrefs)

                banners = page.locator("a.campaign-banner").evaluate_all(
                    """banners => banners.map(banner => ({
                        title: banner.getAttribute('title')
                            || banner.querySelector('img')?.getAttribute('alt')
                            || '',
                        href: banner.href,
                        image: banner.querySelector('img')?.currentSrc
                            || banner.querySelector('img')?.src
                            || '',
                    }))"""
                )
                logger.info(
                    "Farmacia Tei: found %d campaigns in category %d/%d",
                    len(banners),
                    index,
                    len(matching_options),
                )
                for banner in banners:
                    offer = _parse_banner(banner, url, category_name)
                    existing = offers_by_url.get(offer.source_url)
                    if existing is None:
                        offers_by_url[offer.source_url] = offer
                    elif category_name not in existing.category_names:
                        existing.category_names.append(category_name)

            return list(offers_by_url.values())
        finally:
            browser.close()


def _load_category_names() -> list[str]:
    from core_app.models import Category

    return list(
        Category.objects.filter(
            brand__official_website__icontains=FARMACIA_TEI_DOMAIN,
            brand__fl_disabled=False,
            fl_disabled=False,
        )
        .order_by("name")
        .values_list("name", flat=True)
    )


def _match_category_options(
    category_names: Iterable[str], option_labels: Iterable[str]
) -> list[tuple[str, str]]:
    options_by_key = {
        _normalize_category_name(label): label
        for label in option_labels
        if _normalize_category_name(label) != "toate campaniile"
    }
    return [
        (name, options_by_key[key])
        for name in category_names
        if (key := _normalize_category_name(name)) in options_by_key
    ]


def _normalize_category_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_name = decomposed.encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", " ", ascii_name).strip()


def _is_farmacia_tei_url(url: str) -> bool:
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https"} and (
        hostname == FARMACIA_TEI_DOMAIN
        or hostname.endswith(f".{FARMACIA_TEI_DOMAIN}")
    )


def _dismiss_cookie_banner(page: Page) -> None:
    button = page.locator("#CybotCookiebotDialogBodyButtonDecline")
    if button.count() and button.is_visible():
        button.click()
        page.locator("#CybotCookiebotDialog").wait_for(
            state="hidden", timeout=10_000
        )


def _wait_for_category_change(page: Page, previous_hrefs: list[str]) -> None:
    page.wait_for_function(
        """previousHrefs => {
            const status = document.querySelector('#pl-msg');
            const isLoading = status && status.getClientRects().length > 0;
            const hrefs = [...document.querySelectorAll('a.campaign-banner')]
                .map(banner => banner.href);
            return !isLoading && hrefs.join('\\n') !== previousHrefs.join('\\n');
        }""",
        arg=previous_hrefs,
        timeout=REQUEST_TIMEOUT_MS,
    )


def _parse_banner(
    banner: dict[str, str], page_url: str, category_name: str
) -> ScrapedOffer:
    raw_title = banner["title"].strip()
    if not raw_title:
        raise ValueError("Farmacia Tei campaign banner has no title")

    source_url = banner["href"].strip()
    if not source_url or not _is_farmacia_tei_url(source_url):
        raise ValueError(f"Invalid Farmacia Tei campaign URL: {source_url!r}")

    title_without_campaign = re.sub(
        r"\s*[-–.]?\s*zorii\s+reducerilor.*$",
        "",
        raw_title,
        flags=re.IGNORECASE,
    ).strip()
    product = title_without_campaign
    offer_text = ""
    offer_type = ""
    discount_percentage = None
    for offer_type, pattern in _OFFER_PATTERNS:
        match = re.search(pattern, title_without_campaign, flags=re.IGNORECASE)
        if match:
            offer_text = match.group(0).strip()
            percentage_match = re.search(r"(\d+)\s*%", offer_text)
            if percentage_match:
                discount_percentage = Decimal(percentage_match.group(1))
            if "reducere" not in offer_text.casefold():
                offer_text += " reducere"
            product = (
                title_without_campaign[: match.start()]
                + " "
                + title_without_campaign[match.end() :]
            )
            product = re.sub(r"\s+", " ", product).strip(" -–,.")
            break

    return ScrapedOffer(
        title=raw_title,
        source_url=source_url,
        products=[product] if product else [],
        description=offer_text,
        terms=offer_type,
        category_names=[category_name],
        image_url=urljoin(page_url, banner["image"]) if banner["image"] else None,
        discount_percentage=discount_percentage,
    )