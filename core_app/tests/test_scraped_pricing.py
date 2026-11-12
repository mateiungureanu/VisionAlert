from decimal import Decimal

from django.test import SimpleTestCase

from core_app.scraping.scrapers.farmacia_tei import _parse_banner
from core_app.scraping.scrapers.kfc import _validate_offer


class ScrapedPricingTests(SimpleTestCase):
    def test_farmacia_tei_extracts_percentage_discount_from_campaign_title(self):
        offer = _parse_banner(
            {
                "title": "Brand - pana la 25% reducere",
                "href": "https://comenzi.farmaciatei.ro/campanie/brand",
                "image": "",
            },
            "https://comenzi.farmaciatei.ro/eveniment/campanie",
            "Ingrijire",
        )

        self.assertEqual(offer.discount_percentage, Decimal("25"))
        self.assertIsNone(offer.previous_price)
        self.assertIsNone(offer.price)

    def test_kfc_extractor_keeps_prices_and_discount_when_present(self):
        offer = _validate_offer(
            {
                "title": "Meniu promoțional",
                "description": "Reducere la meniu",
                "terms": "",
                "products": ["Meniu"],
                "previous_price": "45 lei",
                "price": "35 lei",
                "discount_percentage": 22.22,
                "valid_from": None,
                "valid_until": None,
            }
        )

        self.assertEqual(offer["previous_price"], "45 lei")
        self.assertEqual(offer["price"], "35 lei")
        self.assertEqual(offer["discount_percentage"], Decimal("22.22"))
