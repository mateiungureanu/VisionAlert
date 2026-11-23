from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core_app.models import Brand, BrandSubscription, FavoriteOffer, Offer, User


class FavoriteOfferTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="saver", email="saver@example.com", password="test-password"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other-saver@example.com", password="test-password"
        )
        self.kfc = Brand.objects.create(name="KFC", official_website="https://kfc.ro")
        self.tei = Brand.objects.create(name="Farmacia Tei", official_website="https://tei.ro")
        self.client.force_authenticate(user=self.user)

    def offer(self, title, brand=None, discount=None, **extra):
        return Offer.objects.create(
            title=title, brand=brand or self.kfc, discount_percentage=discount, **extra
        )

    def save_offer(self, offer, user=None):
        return FavoriteOffer.objects.create(user=user or self.user, offer=offer)

    def titles(self, response):
        return [offer["title"] for offer in response.data["results"]]


class FavoriteOfferModelTests(FavoriteOfferTestCase):
    def test_user_and_offer_can_only_be_paired_once(self):
        offer = self.offer("Burger")
        self.save_offer(offer)

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.save_offer(offer)

    def test_many_users_can_favorite_the_same_offer_and_one_user_many_offers(self):
        first, second = self.offer("Burger"), self.offer("Wings")
        self.save_offer(first)
        self.save_offer(second)
        self.save_offer(first, user=self.other_user)

        self.assertEqual(self.user.favorite_offers.count(), 2)
        self.assertEqual(first.favorited_by.count(), 2)

    def test_deleting_an_offer_or_a_user_removes_the_favorites(self):
        offer = self.offer("Burger")
        self.save_offer(offer)
        self.save_offer(offer, user=self.other_user)

        self.other_user.delete()
        self.assertEqual(FavoriteOffer.objects.count(), 1)
        offer.delete()
        self.assertEqual(FavoriteOffer.objects.count(), 0)


class FavoriteOfferToggleTests(FavoriteOfferTestCase):
    def test_put_adds_the_offer_and_is_idempotent(self):
        offer = self.offer("Burger")
        url = reverse("favorite-offer-toggle", args=[offer.id])

        first = self.client.put(url)
        second = self.client.put(url)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data, {"offer_id": offer.id, "is_favorite": True})
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(FavoriteOffer.objects.filter(user=self.user).count(), 1)

    def test_delete_removes_the_offer_and_is_idempotent(self):
        offer = self.offer("Burger")
        self.save_offer(offer)
        url = reverse("favorite-offer-toggle", args=[offer.id])

        first = self.client.delete(url)
        second = self.client.delete(url)

        self.assertEqual(first.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(second.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FavoriteOffer.objects.exists())

    def test_unknown_offer_returns_404(self):
        response = self.client.put(reverse("favorite-offer-toggle", args=[9999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_only_touches_the_current_users_favorite(self):
        offer = self.offer("Burger")
        self.save_offer(offer, user=self.other_user)

        self.client.delete(reverse("favorite-offer-toggle", args=[offer.id]))

        self.assertTrue(FavoriteOffer.objects.filter(user=self.other_user, offer=offer).exists())

    def test_requires_authentication(self):
        offer = self.offer("Burger")
        self.client.force_authenticate(user=None)

        put = self.client.put(reverse("favorite-offer-toggle", args=[offer.id]))
        delete = self.client.delete(reverse("favorite-offer-toggle", args=[offer.id]))

        self.assertEqual(put.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(delete.status_code, status.HTTP_401_UNAUTHORIZED)


class FavoriteOfferListTests(FavoriteOfferTestCase):
    url = property(lambda self: reverse("favorite-offer-list"))

    def test_lists_only_the_current_users_favorites_newest_saved_first(self):
        old, new, not_mine = self.offer("Old save"), self.offer("New save"), self.offer("Not mine")
        saved_old = self.save_offer(old)
        saved_new = self.save_offer(new)
        FavoriteOffer.objects.filter(pk=saved_old.pk).update(
            created_at=timezone.now() - timedelta(days=2)
        )
        FavoriteOffer.objects.filter(pk=saved_new.pk).update(created_at=timezone.now())
        self.save_offer(not_mine, user=self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.data["count"], 2)
        self.assertEqual(self.titles(response), ["New save", "Old save"])

    def test_keeps_expired_offers_and_offers_from_unsubscribed_brands(self):
        expired = self.offer("Expired", valid_until=timezone.now() - timedelta(days=1))
        self.save_offer(expired)
        self.assertFalse(BrandSubscription.objects.filter(user=self.user).exists())

        response = self.client.get(self.url)

        self.assertEqual(self.titles(response), ["Expired"])

    def test_every_listed_offer_is_marked_as_favorite(self):
        self.save_offer(self.offer("Burger"))

        response = self.client.get(self.url)

        self.assertTrue(response.data["results"][0]["is_favorite"])

    def test_filters_by_brand_search_and_discount(self):
        for title, brand, discount in [
            ("Zinger menu", self.kfc, Decimal("20.00")),
            ("Bucket", self.kfc, Decimal("55.00")),
            ("Vitamina C", self.tei, Decimal("20.00")),
            ("Plain", self.tei, None),
        ]:
            self.save_offer(self.offer(title, brand, discount))

        by_brand = self.client.get(self.url, {"brands": str(self.tei.id)})
        by_search = self.client.get(self.url, {"search": " ZINGER "})
        by_discount = self.client.get(self.url, {"discounts": "20,none"})
        combined = self.client.get(
            self.url, {"brands": str(self.kfc.id), "discounts": "50"}
        )

        self.assertEqual(set(self.titles(by_brand)), {"Vitamina C", "Plain"})
        self.assertEqual(self.titles(by_search), ["Zinger menu"])
        self.assertEqual(set(self.titles(by_discount)), {"Zinger menu", "Vitamina C", "Plain"})
        self.assertEqual(self.titles(combined), ["Bucket"])

    def test_invalid_brand_filter_returns_nothing(self):
        self.save_offer(self.offer("Burger"))

        response = self.client.get(self.url, {"brands": "abc"})

        self.assertEqual(response.data["count"], 0)

    def test_paginates_results(self):
        for index in range(14):
            self.save_offer(self.offer(f"Offer {index}"))

        first = self.client.get(self.url)
        second = self.client.get(self.url, {"page": 2})

        self.assertEqual(first.data["count"], 14)
        self.assertEqual(len(first.data["results"]), 12)
        self.assertEqual(len(second.data["results"]), 2)

    def test_empty_for_a_user_without_favorites(self):
        response = self.client.get(self.url)

        self.assertEqual(response.data["count"], 0)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FavoriteOfferFacetTests(FavoriteOfferTestCase):
    def setUp(self):
        super().setUp()
        for title, brand, discount in [
            ("Zinger menu", self.kfc, Decimal("20.00")),
            ("Bucket", self.kfc, Decimal("55.00")),
            ("Vitamina C", self.tei, Decimal("25.00")),
            ("Plain", self.tei, None),
        ]:
            self.save_offer(self.offer(title, brand, discount))
        self.save_offer(self.offer("Hidden", self.kfc, Decimal("10.00")), user=self.other_user)

    def test_brand_facets_list_brands_with_counts_sorted_by_name(self):
        response = self.client.get(reverse("favorite-offer-brand-facets"))

        self.assertEqual(
            response.data,
            [
                {"id": self.tei.id, "name": "Farmacia Tei", "count": 2},
                {"id": self.kfc.id, "name": "KFC", "count": 2},
            ],
        )

    def test_brand_facets_follow_search_and_discounts_but_not_brands(self):
        response = self.client.get(
            reverse("favorite-offer-brand-facets"),
            {"discounts": "20", "brands": str(self.kfc.id)},
        )

        self.assertEqual(
            response.data,
            [
                {"id": self.tei.id, "name": "Farmacia Tei", "count": 1},
                {"id": self.kfc.id, "name": "KFC", "count": 1},
            ],
        )

    def test_discount_facets_list_existing_bands_only(self):
        response = self.client.get(reverse("favorite-offer-discount-facets"))

        self.assertEqual(
            response.data,
            [
                {"key": "20", "count": 2},
                {"key": "50", "count": 1},
                {"key": "none", "count": 1},
            ],
        )

    def test_discount_facets_follow_brands_but_not_discounts(self):
        response = self.client.get(
            reverse("favorite-offer-discount-facets"),
            {"brands": str(self.tei.id), "discounts": "50"},
        )

        self.assertEqual(
            response.data,
            [{"key": "20", "count": 1}, {"key": "none", "count": 1}],
        )

    def test_facets_require_authentication(self):
        self.client.force_authenticate(user=None)

        brands = self.client.get(reverse("favorite-offer-brand-facets"))
        discounts = self.client.get(reverse("favorite-offer-discount-facets"))

        self.assertEqual(brands.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(discounts.status_code, status.HTTP_401_UNAUTHORIZED)


class OfferIsFavoriteFlagTests(FavoriteOfferTestCase):
    def test_home_feeds_flag_offers_the_user_saved(self):
        BrandSubscription.objects.create(user=self.user, brand=self.kfc, is_favorite=True)
        saved, unsaved = self.offer("Saved"), self.offer("Unsaved")
        self.save_offer(saved)
        self.save_offer(unsaved, user=self.other_user)

        mine = self.client.get(reverse("my-offers"))
        feed = self.client.get(reverse("favorite-offers"))

        flags = {offer["title"]: offer["is_favorite"] for offer in mine.data}
        self.assertEqual(flags, {"Saved": True, "Unsaved": False})
        feed_flags = {offer["title"]: offer["is_favorite"] for offer in feed.data["results"]}
        self.assertEqual(feed_flags, {"Saved": True, "Unsaved": False})
