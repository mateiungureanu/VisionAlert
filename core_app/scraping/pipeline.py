from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from time import perf_counter
from urllib.parse import urlsplit

from django.db import connections, transaction
from django.utils import timezone

from core_app.models import Brand, Category, Offer, OfferSource
from core_app.scraping.contracts import ScrapedOffer
from core_app.scraping.notifications import OfferChange, send_offer_summaries
from core_app.scraping.scrapers.cinemacity import scrape_cinemacity_offers
from core_app.scraping.scrapers.farmacia_tei import scrape_farmacia_tei_offers
from core_app.scraping.scrapers.intersport import scrape_intersport_offers
from core_app.scraping.scrapers.kfc import scrape_kfc_offers

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineSummary:
    scraped: int
    created: int
    updated: int
    skipped_brands: tuple[str, ...]
    priced_offers: int
    images_not_persisted: int
    emails_sent: int


_SCRAPERS = (
    ("Cinemacity", "cinemacity.ro"),
    ("Farmacia Tei", "farmaciatei.ro"),
    ("KFC", "kfc.ro"),
    ("Intersport", "intersport.ro"),
)


def run_pipeline(*, email_backend: str | None = None) -> PipelineSummary:
    started_at = perf_counter()
    logger.info("Scraping pipeline started")
    brands = _load_brands()
    scrapers = {
        "cinemacity": scrape_cinemacity_offers,
        "farmacia tei": scrape_farmacia_tei_offers,
        "kfc": scrape_kfc_offers,
        "intersport": scrape_intersport_offers,
    }
    skipped_brands: list[str] = []
    scraped_by_brand: list[tuple[Brand, list[ScrapedOffer], str]] = []

    for brand_name, domain in _SCRAPERS:
        brand = brands.get(brand_name.casefold())
        if brand is None:
            raise ValueError(f"Required brand is not registered: {brand_name}")
        if brand.fl_disabled:
            skipped_brands.append(brand.name)
            logger.info("%s: skipped (brand is disabled)", brand.name)
            continue

        scraper = scrapers[brand_name.casefold()]
        logger.info("%s: scraping started", brand.name)
        scraper_started_at = perf_counter()
        try:
            offers = scraper()
        except Exception:
            logger.exception("%s: scraping failed", brand.name)
            raise
        finally:
            connections.close_all()
        scraped_by_brand.append((brand, offers, domain))
        logger.info(
            "%s: scraping completed; %d offers in %.1f seconds",
            brand.name,
            len(offers),
            perf_counter() - scraper_started_at,
        )

    connections.close_all()

    created = 0
    updated = 0
    priced_offer_count = 0
    image_count = 0
    changes: list[OfferChange] = []
    scraped_count = sum(len(offers) for _, offers, _ in scraped_by_brand)

    logger.info("Saving %d scraped offers to the database", scraped_count)
    try:
        with transaction.atomic():
            locked_brands = {
                brand.pk: brand
                for brand in Brand.objects.select_for_update()
                .filter(pk__in=[brand.pk for brand, _, _ in scraped_by_brand])
                .order_by("pk")
            }
            for brand, offers, domain in scraped_by_brand:
                locked_brand = locked_brands[brand.pk]
                if locked_brand.fl_disabled:
                    raise ValueError(
                        f"{locked_brand.name} was disabled while the pipeline was running"
                    )
                for index, scraped in enumerate(offers, start=1):
                    _validate_scraped_offer(scraped, domain)
                    offer, was_created, was_improved = _save_offer(
                        locked_brand, scraped
                    )
                    if was_created:
                        created += 1
                        change_type = "new"
                    else:
                        updated += 1
                        change_type = "improved" if was_improved else None
                    if change_type is not None:
                        changes.append(
                            OfferChange(
                                brand_id=locked_brand.pk,
                                brand_name=locked_brand.name,
                                offer_id=offer.pk,
                                change_type=change_type,
                                categories=tuple(
                                    offer.categories.order_by("name").values_list(
                                        "pk", "name"
                                    )
                                ),
                            )
                        )
                    priced_offer_count += any(
                        value is not None
                        for value in (
                            scraped.previous_price,
                            scraped.price,
                            scraped.discount_percentage,
                        )
                    )
                    image_count += scraped.image_url is not None
                    if index == len(offers) or index % 10 == 0:
                        logger.info(
                            "%s: saved %d/%d offers",
                            brand.name,
                            index,
                            len(offers),
                        )
    except Exception:
        logger.exception("Saving offers failed; database transaction rolled back")
        raise

    emails_sent = send_offer_summaries(changes, email_backend=email_backend)
    summary = PipelineSummary(
        scraped=scraped_count,
        created=created,
        updated=updated,
        skipped_brands=tuple(skipped_brands),
        priced_offers=priced_offer_count,
        images_not_persisted=image_count,
        emails_sent=emails_sent,
    )
    logger.info(
        "Scraping pipeline completed in %.1f seconds: %d scraped, %d created, "
        "%d updated, %d summary emails sent",
        perf_counter() - started_at,
        summary.scraped,
        summary.created,
        summary.updated,
        summary.emails_sent,
    )
    return summary


def _load_brands() -> dict[str, Brand]:
    return {
        brand.name.casefold(): brand
        for brand in Brand.objects.all()
        if brand.name.casefold()
        in {brand_name.casefold() for brand_name, _ in _SCRAPERS}
    }


def _validate_scraped_offer(scraped: ScrapedOffer, domain: str) -> None:
    if not scraped.title.strip():
        raise ValueError("A scraper returned an offer with an empty title")
    parsed_url = urlsplit(scraped.source_url)
    hostname = (parsed_url.hostname or "").lower().rstrip(".")
    if parsed_url.scheme not in {"http", "https"} or not (
        hostname == domain or hostname.endswith(f".{domain}")
    ):
        raise ValueError(
            f"Offer source URL does not belong to {domain}: {scraped.source_url!r}"
        )
    if any(not isinstance(product, str) for product in scraped.products):
        raise ValueError(
            f"Offer {scraped.title!r} contains a non-text product value"
        )
    for field_name, value in (
        ("previous_price", scraped.previous_price),
        ("price", scraped.price),
    ):
        if value is not None and not isinstance(value, str):
            raise ValueError(
                f"Offer {scraped.title!r} has a non-text {field_name}"
            )
    if scraped.discount_percentage is not None and (
        not isinstance(scraped.discount_percentage, Decimal)
        or not scraped.discount_percentage.is_finite()
        or not Decimal("0") <= scraped.discount_percentage <= Decimal("100")
    ):
        raise ValueError(
            f"Offer {scraped.title!r} has an invalid discount percentage"
        )


def _save_offer(
    brand: Brand, scraped: ScrapedOffer
) -> tuple[Offer, bool, bool]:
    sources = list(
        OfferSource.objects.select_for_update()
        .filter(url=scraped.source_url)
        .select_related("offer")
    )
    matching_sources = [source for source in sources if source.offer.brand_id == brand.pk]
    if len(matching_sources) > 1:
        raise ValueError(
            f"Multiple {brand.name} offers use source URL {scraped.source_url!r}"
        )
    if sources and not matching_sources:
        raise ValueError(
            f"Offer source URL is already assigned to another brand: "
            f"{scraped.source_url!r}"
        )

    if matching_sources:
        offer = matching_sources[0].offer
        created = False
    else:
        offer = Offer(brand=brand)
        created = True

    scraped_previous_price = _parse_price(scraped.previous_price, "previous_price")
    scraped_price = _parse_price(scraped.price, "price")
    improved = not created and (
        (
            offer.price is not None
            and scraped_price is not None
            and scraped_price < offer.price
        )
        or (
            offer.discount_percentage is not None
            and scraped.discount_percentage is not None
            and scraped.discount_percentage > offer.discount_percentage
        )
    )

    offer.title = scraped.title.strip()
    offer.description = scraped.description
    offer.products = scraped.products
    offer.terms = scraped.terms
    if scraped_previous_price is not None:
        offer.previous_price = scraped_previous_price
    if scraped_price is not None:
        offer.price = scraped_price
    if scraped.discount_percentage is not None:
        offer.discount_percentage = scraped.discount_percentage
    offer.valid_from = _make_aware_if_needed(scraped.valid_from)
    offer.valid_until = _make_aware_if_needed(scraped.valid_until)
    offer.save()
    OfferSource.objects.get_or_create(
        offer=offer,
        url=scraped.source_url,
        defaults={"source_type": OfferSource.SourceType.WEBSITE},
    )

    if scraped.category_names:
        categories = []
        for category_name in scraped.category_names:
            matches = list(
                Category.objects.filter(
                    brand=brand,
                    fl_disabled=False,
                    name__iexact=category_name,
                )
            )
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one enabled {brand.name} category named "
                    f"{category_name!r}, found {len(matches)}"
                )
            categories.append(matches[0])
        offer.categories.set(categories)

    return offer, created, improved


_PRICE_NUMBER_PATTERN = re.compile(r"(?<![\w])\d+(?:[\s.,]\d+)*(?![\w])")


def _parse_price(value: str | None, field_name: str) -> Decimal | None:
    if value is None or not value.strip():
        return None

    normalized_value = value.replace("\u00a0", " ").replace("\u202f", " ")
    matches = _PRICE_NUMBER_PATTERN.findall(normalized_value)
    if len(matches) != 1:
        raise ValueError(
            f"Expected one numeric amount for {field_name}, got {value!r}"
        )

    amount = matches[0].replace(" ", "")
    if "," in amount and "." in amount:
        decimal_separator = "," if amount.rfind(",") > amount.rfind(".") else "."
        grouping_separator = "." if decimal_separator == "," else ","
        amount = amount.replace(grouping_separator, "")
        if decimal_separator == ",":
            amount = amount.replace(",", ".")
    elif "," in amount:
        amount = amount.replace(",", ".")
    elif amount.count(".") > 1:
        parts = amount.split(".")
        if any(len(part) != 3 for part in parts[1:]):
            raise ValueError(f"Ambiguous numeric amount for {field_name}: {value!r}")
        amount = "".join(parts)
    elif "." in amount:
        whole, fraction = amount.split(".")
        if len(fraction) == 3 and len(whole) <= 3:
            amount = whole + fraction

    try:
        parsed = Decimal(amount)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid numeric amount for {field_name}: {value!r}") from exc
    normalized_price = parsed.normalize()
    if (
        not parsed.is_finite()
        or parsed < 0
        or normalized_price.as_tuple().exponent < -2
        or parsed.adjusted() > 7
    ):
        raise ValueError(f"Invalid monetary amount for {field_name}: {value!r}")
    return parsed.quantize(Decimal("0.01"))


def _make_aware_if_needed(value: datetime | None) -> datetime | None:
    if value is not None and timezone.is_naive(value):
        return timezone.make_aware(value)
    return value