from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

from django.conf import settings
from django.core.mail import get_connection, send_mail

from core_app.models import BrandSubscription

logger = logging.getLogger("core_app.scraping.pipeline")


@dataclass(frozen=True)
class OfferChange:
    brand_id: int
    brand_name: str
    offer_id: int
    change_type: Literal["new", "improved"]
    categories: tuple[tuple[int, str], ...]


@dataclass
class _CategorySummary:
    name: str
    new_offer_ids: set[int] = field(default_factory=set)
    improved_offer_ids: set[int] = field(default_factory=set)


@dataclass
class _BrandSummary:
    name: str
    new_offer_ids: set[int] = field(default_factory=set)
    improved_offer_ids: set[int] = field(default_factory=set)
    categories: dict[int | None, _CategorySummary] = field(default_factory=dict)


def send_offer_summaries(
    changes: list[OfferChange],
    email_backend: str | None = None,
) -> int:
    if not changes:
        logger.info(
            "No new or improved offers detected; no summary emails to send"
        )
        return 0

    connection = get_connection(backend=email_backend)
    subscriptions = (
        BrandSubscription.objects.filter(
            user__is_active=True,
            user__fl_deleted=False,
            brand__fl_disabled=False,
        )
        .select_related("user", "brand")
        .prefetch_related("categories")
        .order_by("user_id", "brand_id")
    )
    subscriptions_by_user: dict[int, list[BrandSubscription]] = defaultdict(list)
    for subscription in subscriptions:
        subscriptions_by_user[subscription.user_id].append(subscription)

    if not subscriptions_by_user:
        logger.info(
            "Detected %d new or improved offers, but no active user subscriptions "
            "were found; no summary emails to send",
            len(changes),
        )
        return 0

    sent_count = 0
    eligible_users = 0
    for user_subscriptions in subscriptions_by_user.values():
        user = user_subscriptions[0].user
        summaries = _build_user_summary(user_subscriptions, changes)
        if not summaries:
            continue

        eligible_users += 1
        subject = "VisionAlert: noutati la ofertele urmărite"
        message = _format_summary(summaries)
        try:
            sent = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                connection=connection,
            )
        except Exception:
            logger.exception(
                "Could not send offer summary to user %s",
                user.pk,
            )
            continue

        if sent != 1:
            logger.error("Email backend did not send summary to user %s", user.pk)
            continue
        sent_count += 1
        logger.info("Sent offer summary to user %s", user.pk)

    if eligible_users == 0:
        logger.info(
            "Detected %d new or improved offers, but no active subscribers "
            "matched their brands and categories; no summary emails to send",
            len(changes),
        )
    elif sent_count < eligible_users:
        logger.warning(
            "Sent %d of %d eligible offer summary emails",
            sent_count,
            eligible_users,
        )

    return sent_count


def _build_user_summary(
    subscriptions: list[BrandSubscription],
    changes: list[OfferChange],
) -> list[_BrandSummary]:
    subscriptions_by_brand = {item.brand_id: item for item in subscriptions}
    summaries: dict[int, _BrandSummary] = {}

    for change in changes:
        subscription = subscriptions_by_brand.get(change.brand_id)
        if subscription is None:
            continue

        selected_categories = {
            category.pk
            for category in subscription.categories.all()
            if not category.fl_disabled
        }
        category_names = dict(change.categories)
        if selected_categories:
            matching_category_ids = selected_categories.intersection(category_names)
            if category_names and not matching_category_ids:
                continue
            if category_names:
                report_categories = [
                    (category_id, category_names[category_id])
                    for category_id in sorted(matching_category_ids)
                ]
            else:
                report_categories = [(None, "Fără categorie")]
        else:
            report_categories = (
                list(change.categories)
                if change.categories
                else [(None, "Fără categorie")]
            )

        brand_summary = summaries.setdefault(
            change.brand_id, _BrandSummary(name=change.brand_name)
        )
        if change.change_type == "new":
            brand_summary.new_offer_ids.add(change.offer_id)
        else:
            brand_summary.improved_offer_ids.add(change.offer_id)

        for category_id, category_name in report_categories:
            category_summary = brand_summary.categories.setdefault(
                category_id, _CategorySummary(name=category_name)
            )
            if change.change_type == "new":
                category_summary.new_offer_ids.add(change.offer_id)
            else:
                category_summary.improved_offer_ids.add(change.offer_id)

    return sorted(summaries.values(), key=lambda summary: summary.name.casefold())


def _format_summary(summaries: list[_BrandSummary]) -> str:
    lines = [
        "Am găsit oferte noi sau îmbunătățite pentru brandurile urmărite:",
        "",
    ]
    for brand in summaries:
        new_count = len(brand.new_offer_ids)
        improved_count = len(brand.improved_offer_ids)
        lines.append(brand.name)
        lines.append(
            f"  Total: {_offer_count(new_count, 'nouă', 'noi')}; "
            f"{_offer_count(improved_count, 'îmbunătățită', 'îmbunătățite')}."
        )
        categories = sorted(
            brand.categories.values(),
            key=lambda category: category.name.casefold(),
        )
        for category in categories:
            category_new = len(category.new_offer_ids)
            category_improved = len(category.improved_offer_ids)
            lines.append(
                f"  - {category.name}: "
                f"{_offer_count(category_new, 'nouă', 'noi')}; "
                f"{_offer_count(category_improved, 'îmbunătățită', 'îmbunătățite')}."
            )
        lines.append("")

    return "\n".join(lines).rstrip()


def _offer_count(count: int, singular: str, plural: str) -> str:
    return f"{count} ofertă {singular}" if count == 1 else f"{count} oferte {plural}"
