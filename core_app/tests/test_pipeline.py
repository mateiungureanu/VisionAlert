import warnings
from datetime import datetime
from decimal import Decimal
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.db import connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from core_app.models import (
    Brand,
    BrandSubscription,
    Category,
    Offer,
    OfferSource,
    User,
)
from core_app.scraping.contracts import ScrapedOffer
from core_app.scraping.pipeline import _parse_price, run_pipeline


class PipelineTests(TransactionTestCase):
    def setUp(self):
        self.cinemacity = Brand.objects.create(
            name="Cinemacity",
            official_website="https://www.cinemacity.ro/static/ro/ro/offers",
        )
        self.farmacia_tei = Brand.objects.create(
            name="Farmacia Tei",
            official_website="https://comenzi.farmaciatei.ro",
        )
        self.kfc = Brand.objects.create(
            name="KFC",
            official_website="https://kfc.ro/ofertepebune",
        )
        self.intersport = Brand.objects.create(
            name="Intersport",
            official_website="https://www.intersport.ro/sale/",
        )
        self.category = Category.objects.create(
            brand=self.farmacia_tei,
            name="Ingrijire personala",
            url="https://comenzi.farmaciatei.ro/ingrijire-personala",
        )
        self.intersport_category = Category.objects.create(
            brand=self.intersport,
            name="Incaltaminte",
            url="https://www.intersport.ro/sale/incaltaminte-sale/",
        )

    @patch("core_app.scraping.pipeline.scrape_intersport_offers")
    @patch("core_app.scraping.pipeline.scrape_kfc_offers")
    @patch("core_app.scraping.pipeline.scrape_farmacia_tei_offers")
    @patch("core_app.scraping.pipeline.scrape_cinemacity_offers")
    def test_runs_four_scrapers_and_persists_offers_idempotently(
        self, cinemacity_scraper, farmacia_tei_scraper, kfc_scraper, intersport_scraper
    ):
        cinemacity_scraper.return_value = [
            self._offer(
                "Cinema deal",
                "https://www.cinemacity.ro/offers/deal",
                price="10 lei",
                previous_price="15 lei",
                discount_percentage=Decimal("33.33"),
                image_url="https://www.cinemacity.ro/images/deal.jpg",
            )
        ]
        farmacia_tei_scraper.return_value = [
            self._offer(
                "Farmacia Tei deal",
                "https://comenzi.farmaciatei.ro/campanie/deal",
                category_names=[self.category.name],
            )
        ]
        kfc_scraper.return_value = [
            self._offer("KFC deal", "https://kfc.ro/oferte/deal")
        ]
        intersport_scraper.return_value = [
            self._offer(
                "Intersport deal",
                "https://www.intersport.ro/sale/incaltaminte-sale/deal_123/",
                category_names=[self.intersport_category.name],
            )
        ]

        with (
            patch(
                "core_app.scraping.pipeline.connections.close_all",
                wraps=connections.close_all,
            ) as close_all,
            self.assertLogs("core_app.scraping.pipeline", level="INFO") as logs,
        ):
            first_run = run_pipeline()

        self.assertIn("Scraping pipeline started", logs.output[0])
        self.assertTrue(
            any("Cinemacity: scraping completed" in line for line in logs.output)
        )
        self.assertTrue(
            any("Saving 4 scraped offers" in line for line in logs.output)
        )
        self.assertEqual(first_run.scraped, 4)
        self.assertEqual(first_run.created, 4)
        self.assertEqual(first_run.updated, 0)
        self.assertEqual(first_run.priced_offers, 1)
        self.assertEqual(first_run.images_not_persisted, 1)
        self.assertEqual(Offer.objects.count(), 4)
        self.assertEqual(OfferSource.objects.count(), 4)
        cinema_offer = Offer.objects.get(title="Cinema deal")
        self.assertEqual(str(cinema_offer.previous_price), "15.00")
        self.assertEqual(str(cinema_offer.price), "10.00")
        self.assertEqual(str(cinema_offer.discount_percentage), "33.33")
        farmacia_offer = Offer.objects.get(title="Farmacia Tei deal")
        self.assertEqual(list(farmacia_offer.categories.all()), [self.category])
        intersport_offer = Offer.objects.get(title="Intersport deal")
        self.assertEqual(
            list(intersport_offer.categories.all()), [self.intersport_category]
        )
        self.assertEqual(close_all.call_count, 5)

        second_run = run_pipeline()

        self.assertEqual(second_run.created, 0)
        self.assertEqual(second_run.updated, 4)
        self.assertEqual(Offer.objects.count(), 4)
        self.assertEqual(OfferSource.objects.count(), 4)
        cinemacity_scraper.assert_called()
        farmacia_tei_scraper.assert_called()
        kfc_scraper.assert_called()
        intersport_scraper.assert_called()

    def test_parses_romanian_price_formats(self):
        self.assertEqual(_parse_price("1.299,99 lei", "price"), Decimal("1299.99"))
        self.assertEqual(_parse_price("1 299,50 RON", "price"), Decimal("1299.50"))
        self.assertEqual(_parse_price("1.299 lei", "price"), Decimal("1299.00"))
        self.assertEqual(_parse_price("10 lei", "price"), Decimal("10.00"))

    def test_rejects_price_text_with_multiple_amounts(self):
        with self.assertRaisesRegex(ValueError, "Expected one numeric amount"):
            _parse_price("10 lei - 20 lei", "price")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="alerts@example.test",
    )
    @patch("core_app.scraping.pipeline.scrape_intersport_offers")
    @patch("core_app.scraping.pipeline.scrape_kfc_offers")
    @patch("core_app.scraping.pipeline.scrape_farmacia_tei_offers")
    @patch("core_app.scraping.pipeline.scrape_cinemacity_offers")
    def test_sends_one_summary_for_new_and_improved_offers(
        self, cinemacity_scraper, farmacia_tei_scraper, kfc_scraper, intersport_scraper
    ):
        user = User.objects.create_user(
            username="alerts-user",
            email="alerts@example.test",
            password="test-password",
        )
        BrandSubscription.objects.create(user=user, brand=self.cinemacity)
        farmacia_subscription = BrandSubscription.objects.create(
            user=user,
            brand=self.farmacia_tei,
        )
        farmacia_subscription.categories.add(self.category)

        cinema_url = "https://www.cinemacity.ro/offers/deal"
        farmacia_url = "https://comenzi.farmaciatei.ro/campanie/deal"
        cinemacity_scraper.return_value = [
            self._offer("Cinema deal", cinema_url, price="10 lei")
        ]
        farmacia_tei_scraper.return_value = [
            self._offer(
                "Farmacia deal",
                farmacia_url,
                discount_percentage=Decimal("10"),
                category_names=[self.category.name],
            )
        ]
        kfc_scraper.return_value = []
        intersport_scraper.return_value = []

        first_summary = run_pipeline()

        self.assertEqual(first_summary.emails_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Cinemacity", mail.outbox[0].body)
        self.assertIn("Ingrijire personala: 1 ofertă nouă", mail.outbox[0].body)
        self.assertIn("Fără categorie: 1 ofertă nouă", mail.outbox[0].body)

        mail.outbox.clear()
        cinemacity_scraper.return_value = [
            self._offer("Cinema deal", cinema_url, price="8 lei")
        ]
        farmacia_tei_scraper.return_value = [
            self._offer(
                "Farmacia deal",
                farmacia_url,
                discount_percentage=Decimal("15"),
                category_names=[self.category.name],
            )
        ]

        second_summary = run_pipeline()

        self.assertEqual(second_summary.created, 0)
        self.assertEqual(second_summary.emails_sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Cinemacity", mail.outbox[0].body)
        self.assertIn(
            "Ingrijire personala: 0 oferte noi; 1 ofertă îmbunătățită",
            mail.outbox[0].body,
        )
        self.assertNotIn("1 ofertă nouă", mail.outbox[0].body)

        mail.outbox.clear()
        with self.assertLogs("core_app.scraping.pipeline", level="INFO") as logs:
            third_summary = run_pipeline()

        self.assertEqual(third_summary.emails_sent, 0)
        self.assertEqual(mail.outbox, [])
        self.assertTrue(
            any(
                "No new or improved offers detected" in line
                for line in logs.output
            )
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    @patch("core_app.management.commands.scrape_offers.run_pipeline")
    def test_scrape_command_defaults_to_console_email_backend(self, run_pipeline_mock):
        from core_app.scraping.pipeline import PipelineSummary

        run_pipeline_mock.return_value = PipelineSummary(
            scraped=0,
            created=0,
            updated=0,
            skipped_brands=(),
            priced_offers=0,
            images_not_persisted=0,
            emails_sent=0,
        )

        call_command("scrape_offers", stdout=StringIO())

        run_pipeline_mock.assert_called_once_with(
            email_backend="django.core.mail.backends.console.EmailBackend"
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
        DEFAULT_FROM_EMAIL="alerts@example.test",
    )
    def test_console_backend_prints_summary_email(self):
        user = User.objects.create_user(
            username="console-alerts",
            email="console-alerts@example.test",
            password="test-password",
        )
        BrandSubscription.objects.create(user=user, brand=self.cinemacity)
        from core_app.scraping.notifications import OfferChange, send_offer_summaries

        output = StringIO()
        with redirect_stdout(output):
            sent = send_offer_summaries(
                [
                    OfferChange(
                        brand_id=self.cinemacity.pk,
                        brand_name=self.cinemacity.name,
                        offer_id=1,
                        change_type="new",
                        categories=(),
                    )
                ],
                email_backend="django.core.mail.backends.console.EmailBackend",
            )

        self.assertEqual(sent, 1)
        self.assertIn("Subject: =?utf-8?", output.getvalue())
        self.assertIn("To: console-alerts@example.test", output.getvalue())
        self.assertIn("Cinemacity", output.getvalue())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_logs_when_changes_have_no_eligible_subscribers(self):
        user = User.objects.create_user(
            username="unrelated-subscriber",
            email="unrelated@example.test",
            password="test-password",
        )
        BrandSubscription.objects.create(user=user, brand=self.kfc)
        from core_app.scraping.notifications import OfferChange, send_offer_summaries

        with self.assertLogs("core_app.scraping.pipeline", level="INFO") as logs:
            sent = send_offer_summaries(
                [
                    OfferChange(
                        brand_id=self.cinemacity.pk,
                        brand_name=self.cinemacity.name,
                        offer_id=1,
                        change_type="new",
                        categories=(),
                    )
                ]
            )

        self.assertEqual(sent, 0)
        self.assertTrue(
            any("no active subscribers matched" in line for line in logs.output)
        )

    @patch("core_app.scraping.pipeline.scrape_intersport_offers")
    @patch("core_app.scraping.pipeline.scrape_kfc_offers")
    @patch("core_app.scraping.pipeline.scrape_farmacia_tei_offers")
    @patch("core_app.scraping.pipeline.scrape_cinemacity_offers")
    def test_disabled_brand_is_skipped(
        self,
        cinemacity_scraper,
        farmacia_tei_scraper,
        kfc_scraper,
        intersport_scraper,
    ):
        self.kfc.fl_disabled = True
        self.kfc.save(update_fields=["fl_disabled"])
        cinemacity_scraper.return_value = []
        farmacia_tei_scraper.return_value = []
        intersport_scraper.return_value = []

        summary = run_pipeline()

        self.assertEqual(summary.skipped_brands, ("KFC",))
        kfc_scraper.assert_not_called()

    @patch("core_app.scraping.pipeline.scrape_intersport_offers")
    @patch("core_app.scraping.pipeline.scrape_kfc_offers")
    @patch("core_app.scraping.pipeline.scrape_farmacia_tei_offers")
    @patch("core_app.scraping.pipeline.scrape_cinemacity_offers")
    def test_scraper_failure_does_not_persist_partial_results(
        self, cinemacity_scraper, farmacia_tei_scraper, kfc_scraper, intersport_scraper
    ):
        cinemacity_scraper.return_value = [
            self._offer("Cinema deal", "https://www.cinemacity.ro/offers/deal")
        ]
        farmacia_tei_scraper.side_effect = RuntimeError("Farmacia Tei unavailable")

        with self.assertRaisesRegex(RuntimeError, "Farmacia Tei unavailable"):
            run_pipeline()

        self.assertEqual(Offer.objects.count(), 0)
        kfc_scraper.assert_not_called()
        intersport_scraper.assert_not_called()

    @patch("core_app.scraping.pipeline.scrape_intersport_offers")
    @patch("core_app.scraping.pipeline.scrape_kfc_offers")
    @patch("core_app.scraping.pipeline.scrape_farmacia_tei_offers")
    @patch("core_app.scraping.pipeline.scrape_cinemacity_offers")
    def test_naive_offer_dates_are_saved_as_aware_without_runtime_warning(
        self, cinemacity_scraper, farmacia_tei_scraper, kfc_scraper, intersport_scraper
    ):
        cinemacity_scraper.return_value = [
            self._offer(
                "Cinema deal",
                "https://www.cinemacity.ro/offers/deal",
                valid_until=datetime(2026, 11, 12),
            )
        ]
        farmacia_tei_scraper.return_value = []
        kfc_scraper.return_value = []
        intersport_scraper.return_value = []

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RuntimeWarning)
            run_pipeline()

        self.assertFalse(
            [
                warning
                for warning in caught
                if "Offer.valid_until received a naive datetime" in str(warning.message)
            ]
        )
        offer = Offer.objects.get(title="Cinema deal")
        self.assertTrue(timezone.is_aware(offer.valid_until))
        self.assertEqual(
            timezone.localtime(offer.valid_until).replace(tzinfo=None),
            datetime(2026, 11, 12),
        )

    @staticmethod
    def _offer(title, source_url, **kwargs):
        return ScrapedOffer(
            title=title,
            source_url=source_url,
            **kwargs,
        )
