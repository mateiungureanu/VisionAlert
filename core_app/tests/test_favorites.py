from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core_app.models import Brand, BrandSubscription, Offer, User


class FavoriteBrandTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="fav-user", email="fav@example.com", password="test-password"
        )
        self.other_user = User.objects.create_user(
            username="fav-other", email="other@example.com", password="test-password"
        )
        self.kfc = Brand.objects.create(name="KFC", official_website="https://kfc.ro")
        self.tei = Brand.objects.create(name="Farmacia Tei", official_website="https://tei.ro")
        self.sport = Brand.objects.create(name="Intersport", official_website="https://intersport.ro")
        self.kfc_sub = BrandSubscription.objects.create(user=self.user, brand=self.kfc)
        self.tei_sub = BrandSubscription.objects.create(user=self.user, brand=self.tei)
        self.sport_sub = BrandSubscription.objects.create(user=self.user, brand=self.sport)
        self.client.force_authenticate(user=self.user)

    def test_subscription_is_not_favorite_by_default(self):
        response = self.client.get(reverse("brand-subscription-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item["is_favorite"] is False for item in response.data))

    def test_marks_and_unmarks_favorite(self):
        url = reverse("brand-subscription-favorite", args=[self.kfc.id])

        response = self.client.patch(url, {"is_favorite": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_favorite"])
        self.kfc_sub.refresh_from_db()
        self.assertTrue(self.kfc_sub.is_favorite)

        response = self.client.patch(url, {"is_favorite": False}, format="json")
        self.assertFalse(response.data["is_favorite"])
        self.kfc_sub.refresh_from_db()
        self.assertFalse(self.kfc_sub.is_favorite)

    def test_favorite_requires_boolean_value(self):
        url = reverse("brand-subscription-favorite", args=[self.kfc.id])

        response = self.client.patch(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_favorite_brand_without_subscription(self):
        BrandSubscription.objects.filter(user=self.user, brand=self.sport).delete()

        response = self.client.patch(
            reverse("brand-subscription-favorite", args=[self.sport.id]),
            {"is_favorite": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_change_another_users_subscription(self):
        BrandSubscription.objects.create(user=self.other_user, brand=self.sport, is_favorite=False)
        BrandSubscription.objects.filter(user=self.user, brand=self.sport).delete()

        response = self.client.patch(
            reverse("brand-subscription-favorite", args=[self.sport.id]),
            {"is_favorite": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            BrandSubscription.objects.get(user=self.other_user, brand=self.sport).is_favorite
        )

    def test_resubscribing_keeps_favorite_flag(self):
        self.kfc_sub.is_favorite = True
        self.kfc_sub.save()

        response = self.client.post(
            reverse("brand-subscription-list"), {"brand_id": self.kfc.id}, format="json"
        )

        self.assertTrue(response.data["is_favorite"])


class FavoriteOffersTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="feed-user", email="feed@example.com", password="test-password"
        )
        self.kfc = Brand.objects.create(name="KFC", official_website="https://kfc.ro")
        self.tei = Brand.objects.create(name="Farmacia Tei", official_website="https://tei.ro")
        self.sport = Brand.objects.create(name="Intersport", official_website="https://intersport.ro")
        BrandSubscription.objects.create(user=self.user, brand=self.kfc, is_favorite=True)
        BrandSubscription.objects.create(user=self.user, brand=self.tei, is_favorite=True)
        BrandSubscription.objects.create(user=self.user, brand=self.sport)
        Offer.objects.create(title="KFC offer", brand=self.kfc)
        Offer.objects.create(title="Tei offer", brand=self.tei)
        Offer.objects.create(title="Sport offer", brand=self.sport)
        Offer.objects.create(
            title="Expired KFC",
            brand=self.kfc,
            valid_until=timezone.now() - timedelta(days=1),
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("favorite-offers")

    def test_returns_only_favorite_brand_offers_in_paginated_shape(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(
            {offer["title"] for offer in response.data["results"]},
            {"KFC offer", "Tei offer"},
        )

    def test_filters_by_selected_brands(self):
        response = self.client.get(self.url, {"brands": str(self.kfc.id)})

        self.assertEqual([offer["title"] for offer in response.data["results"]], ["KFC offer"])

    def test_searches_in_title_ignoring_case(self):
        response = self.client.get(self.url, {"search": "  tEi "})

        self.assertEqual([offer["title"] for offer in response.data["results"]], ["Tei offer"])

    def test_search_does_not_match_description(self):
        Offer.objects.create(title="Fara legatura", description="meniu special", brand=self.kfc)

        response = self.client.get(self.url, {"search": "meniu"})

        self.assertEqual(response.data["count"], 0)

    def test_search_combines_with_brand_filter(self):
        response = self.client.get(
            self.url, {"search": "offer", "brands": str(self.tei.id)}
        )

        self.assertEqual([offer["title"] for offer in response.data["results"]], ["Tei offer"])

    def test_brand_filter_ignores_non_favorite_brands(self):
        response = self.client.get(self.url, {"brands": str(self.sport.id)})

        self.assertEqual(response.data["count"], 0)

    def test_invalid_brand_filter_returns_nothing(self):
        response = self.client.get(self.url, {"brands": "abc"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_paginates_results(self):
        for index in range(14):
            Offer.objects.create(title=f"Extra {index}", brand=self.kfc)

        first_page = self.client.get(self.url)
        second_page = self.client.get(self.url, {"page": 2})

        self.assertEqual(first_page.data["count"], 16)
        self.assertEqual(len(first_page.data["results"]), 12)
        self.assertIsNotNone(first_page.data["next"])
        self.assertEqual(len(second_page.data["results"]), 4)
        self.assertIsNone(second_page.data["next"])

    def _discount_offers(self):
        Offer.objects.all().delete()
        for title, brand, discount in [
            ("Small", self.kfc, Decimal("5.00")),
            ("Ten", self.kfc, Decimal("10.00")),
            ("Nineteen", self.tei, Decimal("19.99")),
            ("Thirty three", self.tei, Decimal("33.33")),
            ("Half", self.kfc, Decimal("50.00")),
            ("Huge", self.tei, Decimal("70.00")),
            ("No discount", self.kfc, None),
            ("Not favorite", self.sport, Decimal("25.00")),
        ]:
            Offer.objects.create(title=title, brand=brand, discount_percentage=discount)

    def _titles(self, response):
        return {offer["title"] for offer in response.data["results"]}

    def test_discount_bands_list_only_existing_bands_with_counts(self):
        self._discount_offers()

        response = self.client.get(reverse("favorite-offer-discounts"))

        self.assertEqual(
            response.data,
            [
                {"key": "0", "count": 1},
                {"key": "10", "count": 2},
                {"key": "30", "count": 1},
                {"key": "50", "count": 2},
                {"key": "none", "count": 1},
            ],
        )

    def test_discount_bands_follow_brand_and_search_filters(self):
        self._discount_offers()

        response = self.client.get(
            reverse("favorite-offer-discounts"), {"brands": str(self.tei.id)}
        )

        self.assertEqual(
            [item["key"] for item in response.data], ["10", "30", "50"]
        )

    def test_filters_by_single_discount_band(self):
        self._discount_offers()

        response = self.client.get(self.url, {"discounts": "10"})

        self.assertEqual(self._titles(response), {"Ten", "Nineteen"})

    def test_top_band_is_open_ended(self):
        self._discount_offers()

        response = self.client.get(self.url, {"discounts": "50"})

        self.assertEqual(self._titles(response), {"Half", "Huge"})

    def test_lowest_band_is_below_ten(self):
        self._discount_offers()

        response = self.client.get(self.url, {"discounts": "0"})

        self.assertEqual(self._titles(response), {"Small"})

    def test_filters_by_several_bands_and_no_discount(self):
        self._discount_offers()

        response = self.client.get(self.url, {"discounts": "30,none"})

        self.assertEqual(self._titles(response), {"Thirty three", "No discount"})

    def test_invalid_discount_filter_returns_nothing(self):
        self._discount_offers()

        response = self.client.get(self.url, {"discounts": "abc,15"})

        self.assertEqual(response.data["count"], 0)

    def test_discount_filter_combines_with_brand_filter(self):
        self._discount_offers()

        response = self.client.get(
            self.url, {"discounts": "50", "brands": str(self.kfc.id)}
        )

        self.assertEqual(self._titles(response), {"Half"})

    def test_discount_bands_require_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("favorite-offer-discounts"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_without_favorites_gets_empty_page(self):
        BrandSubscription.objects.filter(user=self.user).update(is_favorite=False)

        response = self.client.get(self.url)

        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
