from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from core_app.models import Brand, Category
from core_app.scraping.scrapers.intersport import (
    _load_categories,
    _parse_product_card,
)


class IntersportScraperTests(SimpleTestCase):
    def test_parses_product_card_prices_discount_image_and_category(self):
        offer = _parse_product_card(
            {
                "title": "adidas PANTOFI TERREX",
                "href": (
                    "https://www.intersport.ro/sale/incaltaminte-sale/"
                    "adidas-pantofi_123/"
                ),
                "image": "//cdn.example.test/product.jpg",
                "price": "349,99",
                "previous_price": "499,99 LEI",
                "discount": "-30%",
            },
            "https://www.intersport.ro/sale/incaltaminte-sale/",
            "Incaltaminte",
        )

        self.assertEqual(offer.title, "adidas PANTOFI TERREX")
        self.assertEqual(offer.products, ["adidas PANTOFI TERREX"])
        self.assertEqual(offer.category_names, ["Incaltaminte"])
        self.assertEqual(offer.price, "349,99")
        self.assertEqual(offer.previous_price, "499,99 LEI")
        self.assertEqual(offer.discount_percentage, Decimal("30"))
        self.assertEqual(offer.image_url, "https://cdn.example.test/product.jpg")

    def test_rejects_product_url_outside_intersport(self):
        with self.assertRaisesRegex(ValueError, "Invalid Intersport product URL"):
            _parse_product_card(
                {
                    "title": "Product",
                    "href": "https://example.test/product",
                    "image": "",
                    "price": "",
                    "previous_price": "",
                    "discount": "",
                },
                "https://www.intersport.ro/sale/",
                "Sale",
            )


class IntersportCategoryTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="Intersport",
            official_website="https://www.intersport.ro/sale/",
        )

    def test_loads_enabled_categories_and_their_database_urls(self):
        category = Category.objects.create(
            brand=self.brand,
            name="Incaltaminte",
            url="https://www.intersport.ro/sale/incaltaminte-sale/",
        )
        Category.objects.create(
            brand=self.brand,
            name="Disabled",
            url="https://www.intersport.ro/sale/disabled/",
            fl_disabled=True,
        )

        self.assertEqual(
            _load_categories(),
            [(category.name, category.url)],
        )

    def test_rejects_enabled_categories_without_a_database_url(self):
        Category.objects.create(brand=self.brand, name="Missing link")

        with self.assertRaisesRegex(
            ValueError, "has no URL"
        ):
            _load_categories()
