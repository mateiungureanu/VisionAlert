from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core_app.models import (
    Brand,
    BrandSubscription,
    Category,
    Offer,
    OfferSource,
    User,
)


class MyOffersTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="offers-user",
            email="offers@example.com",
            password="test-password",
        )
        self.brand = Brand.objects.create(
            name="Farmacia Tei",
            official_website="https://comenzi.farmaciatei.ro",
        )
        self.other_brand = Brand.objects.create(
            name="KFC",
            official_website="https://kfc.ro",
        )
        self.category = Category.objects.create(
            brand=self.brand,
            name="Ingrijire",
            url="https://comenzi.farmaciatei.ro/ingrijire",
        )
        self.other_category = Category.objects.create(
            brand=self.brand,
            name="Machiaj",
            url="https://comenzi.farmaciatei.ro/machiaj",
        )
        self.subscription = BrandSubscription.objects.create(
            user=self.user,
            brand=self.brand,
        )
        self.subscription.categories.add(self.category)
        BrandSubscription.objects.create(user=self.user, brand=self.other_brand)

        self.matching_offer = self._offer("Matching offer", self.brand)
        self.matching_offer.categories.add(self.category)
        self.unclassified_offer = self._offer("Unclassified offer", self.brand)
        self.other_category_offer = self._offer("Other category offer", self.brand)
        self.other_category_offer.categories.add(self.other_category)
        self.brand_only_offer = self._offer("KFC offer", self.other_brand)
        self.expired_offer = self._offer(
            "Expired offer",
            self.other_brand,
            valid_until=timezone.now() - timedelta(days=1),
        )
        OfferSource.objects.create(
            offer=self.matching_offer,
            source_type=OfferSource.SourceType.WEBSITE,
            url="https://comenzi.farmaciatei.ro/campanie/oferta",
        )
        self.client.force_authenticate(user=self.user)

    def test_lists_only_current_users_matching_and_unclassified_offers(self):
        response = self.client.get(reverse("my-offers"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {offer["title"] for offer in response.data},
            {"Matching offer", "Unclassified offer", "KFC offer"},
        )
        matching = next(
            offer for offer in response.data if offer["title"] == "Matching offer"
        )
        self.assertEqual(matching["brand"], self.brand.name)
        self.assertEqual(matching["brand_id"], self.brand.id)
        self.assertEqual(matching["categories"], [{"id": self.category.id, "name": "Ingrijire"}])
        self.assertIsNone(matching["previous_price"])
        self.assertIsNone(matching["price"])
        self.assertIsNone(matching["discount_percentage"])
        self.assertEqual(
            matching["source_urls"],
            ["https://comenzi.farmaciatei.ro/campanie/oferta"],
        )

    def test_returns_all_brand_offers_when_subscription_has_no_categories(self):
        self.subscription.categories.clear()

        response = self.client.get(reverse("my-offers"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Other category offer", {offer["title"] for offer in response.data})

    def test_returns_price_and_discount_fields(self):
        self.matching_offer.previous_price = Decimal("15.00")
        self.matching_offer.price = Decimal("10.00")
        self.matching_offer.discount_percentage = Decimal("33.33")
        self.matching_offer.save()

        response = self.client.get(reverse("my-offers"))
        matching = next(
            offer for offer in response.data if offer["title"] == "Matching offer"
        )

        self.assertEqual(matching["previous_price"], "15.00")
        self.assertEqual(matching["price"], "10.00")
        self.assertEqual(matching["discount_percentage"], "33.33")

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("my-offers"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_without_subscriptions_sees_no_offers(self):
        other_user = User.objects.create_user(
            username="another-user",
            email="another@example.com",
            password="test-password",
        )
        BrandSubscription.objects.filter(user=self.user).delete()
        other_subscription = BrandSubscription.objects.create(
            user=other_user,
            brand=self.brand,
        )
        other_subscription.categories.add(self.category)
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("my-offers"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    @staticmethod
    def _offer(title, brand, valid_until=None):
        return Offer.objects.create(
            title=title,
            brand=brand,
            valid_until=valid_until,
        )
