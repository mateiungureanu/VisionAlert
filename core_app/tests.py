from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


class AccountAndLoginTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='test-user',
            email='user@example.com',
            password='ValidPassword1!',
            first_name='Test',
            last_name='User',
        )

    def test_user_can_login_with_email_and_password(self):
        response = self.client.post(
            '/api/auth/login/',
            {'identifier': 'user@example.com', 'password': 'ValidPassword1!'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_user_can_login_with_username_and_password(self):
        response = self.client.post(
            '/api/auth/login/',
            {'identifier': 'test-user', 'password': 'ValidPassword1!'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

    def test_authenticated_user_can_anonymize_account(self):
        self.client.force_authenticate(self.user)

        response = self.client.delete(reverse('delete-account'))

        self.assertEqual(response.status_code, 204)
        self.user.refresh_from_db()
        self.assertTrue(self.user.fl_deleted)
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.first_name, '')
        self.assertEqual(self.user.last_name, '')
        self.assertIsNone(self.user.phone)
        self.assertEqual(self.user.email, f'deleted-{self.user.pk}@deleted.invalid')
        self.assertFalse(self.user.has_usable_password())

        login_response = self.client.post(
            '/api/auth/login/',
            {'identifier': self.user.email, 'password': 'ValidPassword1!'},
        )
        self.assertEqual(login_response.status_code, 401)
