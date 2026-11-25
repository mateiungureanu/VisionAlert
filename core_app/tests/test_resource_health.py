from unittest.mock import patch

import requests
from cryptography.fernet import Fernet
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from core_app.management.commands.check_resources import Command
from core_app.models import MonitoredResource, User
from core_app.scraping.health import check_resources


class ResourceHealthTests(TestCase):
    def setUp(self):
        self.resource = MonitoredResource.objects.create(
            name="Steam API",
            resource_type=MonitoredResource.ResourceType.API,
            url="https://api.steampowered.com/ISteamWebAPIUtil/GetServerInfo/v1/",
        )
        self.staff = User.objects.create_user(
            username="admin",
            email="admin@example.test",
            password="test-password",
            is_staff=True,
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    @patch("core_app.scraping.health.requests.get")
    def test_failure_notifies_staff_once_and_recovery_notifies_again(self, get):
        get.side_effect = requests.ConnectionError("connection refused")

        first = check_resources()
        second = check_resources()

        self.assertEqual((first.checked, first.failing), (1, 1))
        self.assertEqual((second.checked, second.failing), (1, 1))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("failing", mail.outbox[0].subject)
        self.resource.refresh_from_db()
        self.assertEqual(
            self.resource.health_status,
            MonitoredResource.HealthStatus.FAILING,
        )
        self.assertTrue(self.resource.last_checked_at)

        get.side_effect = None
        get.return_value.status_code = 200
        recovered = check_resources()

        self.assertEqual((recovered.checked, recovered.healthy), (1, 1))
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("recovered", mail.outbox[1].subject)
        self.resource.refresh_from_db()
        self.assertEqual(
            self.resource.health_status,
            MonitoredResource.HealthStatus.HEALTHY,
        )
        self.assertEqual(self.resource.last_error, "")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        RESOURCE_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode("ascii"),
    )
    @patch("core_app.scraping.health.requests.get")
    def test_api_key_is_encrypted_and_sent_in_configured_header(self, get):
        self.resource.credential_name = "X-API-Key"
        self.resource.credential_prefix = ""
        self.resource.set_api_key("private-token")
        self.resource.save()
        get.return_value.status_code = 200

        summary = check_resources(timeout=4)

        self.assertEqual(summary.healthy, 1)
        self.resource.refresh_from_db()
        self.assertNotIn("private-token", self.resource.api_key_encrypted)
        self.assertEqual(self.resource.get_api_key(), "private-token")
        self.assertEqual(
            get.call_args.kwargs["headers"],
            {"X-API-Key": "private-token"},
        )
        self.assertEqual(get.call_args.kwargs["timeout"], 4)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        RESOURCE_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode("ascii"),
    )
    @patch("core_app.scraping.health.requests.get")
    def test_api_key_can_be_sent_as_a_query_parameter(self, get):
        self.resource.credential_location = MonitoredResource.CredentialLocation.QUERY
        self.resource.credential_name = "key"
        self.resource.credential_prefix = ""
        self.resource.set_api_key("private-token")
        self.resource.save()
        get.return_value.status_code = 200

        summary = check_resources()

        self.assertEqual(summary.healthy, 1)
        self.assertEqual(get.call_args.kwargs["params"], {"key": "private-token"})
        self.assertEqual(mail.outbox, [])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        RESOURCE_CREDENTIAL_ENCRYPTION_KEY="",
    )
    def test_api_key_requires_an_encryption_key(self):
        with self.assertRaisesRegex(
            ImproperlyConfigured,
            "RESOURCE_CREDENTIAL_ENCRYPTION_KEY must be configured",
        ):
            self.resource.set_api_key("private-token")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    @patch("core_app.scraping.health.requests.get")
    def test_http_error_is_recorded_and_notifies_staff(self, get):
        get.return_value.status_code = 503

        summary = check_resources()

        self.assertEqual((summary.checked, summary.failing), (1, 1))
        self.resource.refresh_from_db()
        self.assertEqual(
            self.resource.health_status,
            MonitoredResource.HealthStatus.FAILING,
        )
        self.assertEqual(
            self.resource.last_error,
            "HTTP 503 returned by monitored resource.",
        )
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    @patch("core_app.scraping.health.requests.get")
    def test_disabled_resources_are_not_checked(self, get):
        self.resource.enabled = False
        self.resource.save(update_fields=["enabled"])

        summary = check_resources()

        self.assertEqual(summary.checked, 0)
        get.assert_not_called()

    def test_command_rejects_unbounded_timeouts(self):
        from django.core.management.base import CommandError

        command = Command()
        with self.assertRaises(CommandError):
            command.handle(timeout=0)
