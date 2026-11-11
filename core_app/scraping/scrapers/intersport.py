import logging
import re
from decimal import Decimal
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import sync_playwright

from core_app.scraping.contracts import ScrapedOffer

INTERSPORT_DOMAIN = "intersport.ro"
REQUEST_TIMEOUT_MS = 30_000
logger = logging.getLogger(__name__)


def scrape_intersport_offers() -> list[ScrapedOffer]:
    categories = _load_categories()
    if not categories:
        raise ValueError("No enabled Intersport categories with URLs were found")

    offers_by_url: dict[str, ScrapedOffer] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(locale="ro-RO")
            for category_index, (category_name, category_url) in enumerate(
                categories, start=1
            ):
                logger.info(
                    "Intersport: scraping category %d/%d (%s)",
                    category_index,
                    len(categories),
                    category_name,
                )
                page_url: str | None = category_url
                visited_urls: set[str] = set()
                page_index = 0

                while page_url:
                    if page_url in visited_urls:
                        raise ValueError(
                            f"Intersport pagination loop detected at {page_url!r}"
                        )
                    visited_urls.add(page_url)
                    page_index += 1

                    page.goto(
                        page_url,
                        wait_until="domcontentloaded",
                        timeout=REQUEST_TIMEOUT_MS,
                    )
                    if not _is_intersport_url(page.url):
                        raise ValueError(
                            f"Intersport category redirected outside its domain: "
                            f"{page.url!r}"
                        )
                    page.wait_for_selector(
                        "article.x-product-box", timeout=REQUEST_TIMEOUT_MS
                    )
                    cards = page.locator("article.x-product-box").evaluate_all(
                        """cards => cards.map(card => {
                            const titleLink = card.querySelector(
                                'header.title-container a'
                            );
                            const productLink = card.querySelector(
                                'a.js-select-product'
                            ) || titleLink;
                            const currentPrice = card.querySelector('.current-price');
                            const previousPrice = card.querySelector('.deleted-price');
                            const image = card.querySelector('img');
                            return {
                                title: titleLink?.innerText.trim() || '',
                                href: productLink?.href || '',
                                image: image?.currentSrc || image?.src || '',
                                price: currentPrice?.getAttribute('data-current-price')
                                    || currentPrice?.innerText.trim() || '',
                                previous_price: previousPrice?.innerText.trim() || '',
                                discount: card.querySelector('.tag.discount')
                                    ?.innerText.trim() || '',
                            };
                        })"""
                    )
                    logger.info(
                        "Intersport: found %d products in %s, page %d",
                        len(cards),
                        category_name,
                        page_index,
                    )
                    for card in cards:
                        offer = _parse_product_card(card, page.url, category_name)
                        existing = offers_by_url.get(offer.source_url)
                        if existing is None:
                            offers_by_url[offer.source_url] = offer
                        elif category_name not in existing.category_names:
                            existing.category_names.append(category_name)

                    next_href = page.locator('a[title="next-page"]').get_attribute(
                        "href"
                    )
                    if not next_href:
                        page_url = None
                    else:
                        page_url = urljoin(page.url, next_href)
                        if not _is_intersport_url(page_url):
                            raise ValueError(
                                f"Invalid Intersport pagination URL: {page_url!r}"
                            )
        finally:
            browser.close()

    return list(offers_by_url.values())


def _load_categories() -> list[tuple[str, str]]:
    from core_app.models import Category

    categories = list(
        Category.objects.filter(
            brand__official_website__icontains=INTERSPORT_DOMAIN,
            brand__fl_disabled=False,
            fl_disabled=False,
        )
        .order_by("name")
        .values_list("name", "url")
    )
    validated_categories = []
    for category_name, category_url in categories:
        if not category_url:
            raise ValueError(
                f"Enabled Intersport category {category_name!r} has no URL"
            )
        if not _is_intersport_url(category_url):
            raise ValueError(
                f"Invalid Intersport category URL for {category_name!r}: "
                f"{category_url!r}"
            )
        validated_categories.append((category_name, category_url))
    return validated_categories


def _is_intersport_url(url: str) -> bool:
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    return parsed.scheme in {"http", "https"} and (
        hostname == INTERSPORT_DOMAIN
        or hostname.endswith(f".{INTERSPORT_DOMAIN}")
    )


def _parse_product_card(
    card: dict[str, str], page_url: str, category_name: str
) -> ScrapedOffer:
    title = card["title"].strip()
    if not title:
        raise ValueError("Intersport product card has no title")

    source_url = card["href"].strip()
    if not source_url or not _is_intersport_url(source_url):
        raise ValueError(f"Invalid Intersport product URL: {source_url!r}")

    raw_discount = card["discount"].strip()
    discount_percentage = None
    if raw_discount:
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", raw_discount)
        if not match:
            raise ValueError(f"Invalid Intersport product discount: {raw_discount!r}")
        discount_percentage = Decimal(match.group(1).replace(",", "."))

    price = card["price"].strip() or None
    previous_price = card["previous_price"].strip() or None
    image = card["image"].strip()
    return ScrapedOffer(
        title=title,
        source_url=source_url,
        products=[title],
        category_names=[category_name],
        image_url=urljoin(page_url, image) if image else None,
        price=price,
        previous_price=previous_price,
        discount_percentage=discount_percentage,
    )
