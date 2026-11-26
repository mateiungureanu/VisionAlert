from django.core import mail
from django.test import TestCase, override_settings

from core_app.models import Brand, BrandSubscription, Category, User
from core_app.scraping.notifications import OfferChange, send_offer_summaries


class OfferNotificationTests(TestCase):
    def test_selected_categories_do_not_suppress_brand_alerts(self):
        user = User.objects.create_user(
            username="category-subscriber",
            email="category-subscriber@example.test",
            password="test-password",
        )
        brand = Brand.objects.create(
            name="Farmacia Tei",
            official_website="https://www.farmaciatei.ro",
        )
        subscription = BrandSubscription.objects.create(user=user, brand=brand)
        category = Category.objects.create(brand=brand, name="Selected")
        subscription.categories.add(category)

        with override_settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
            DEFAULT_FROM_EMAIL="alerts@example.test",
        ):
            sent = send_offer_summaries(
                [
                    OfferChange(
                        brand_id=brand.pk,
                        brand_name=brand.name,
                        offer_id=1,
                        change_type="new",
                        categories=((999, "Different category"),),
                    )
                ]
            )

        self.assertEqual(sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Different category", mail.outbox[0].body)
