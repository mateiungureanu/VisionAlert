from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from core_app.models import MonitoredResource, User

logger = logging.getLogger("core_app.scraping.health")


@dataclass(frozen=True)
class HealthCheckSummary:
    checked: int
    healthy: int
    failing: int


def check_resources(*, timeout: int = 10) -> HealthCheckSummary:
    checked = 0
    healthy = 0
    failing = 0

    for resource in MonitoredResource.objects.filter(enabled=True).order_by("pk"):
        checked += 1
        previous_status = resource.health_status
        try:
            _check_resource(resource, timeout)
        except requests.RequestException as error:
            resource.health_status = MonitoredResource.HealthStatus.FAILING
            resource.last_error = _safe_error_message(error, resource.get_api_key())
            failing += 1
            logger.warning(
                "Resource %s health check failed: %s",
                resource.pk,
                resource.last_error,
            )
        else:
            resource.health_status = MonitoredResource.HealthStatus.HEALTHY
            resource.last_error = ""
            healthy += 1

        resource.last_checked_at = timezone.now()
        resource.save(
            update_fields=(
                "health_status",
                "last_checked_at",
                "last_error",
                "updated_at",
            )
        )
        if (
            previous_status != MonitoredResource.HealthStatus.FAILING
            and resource.health_status == MonitoredResource.HealthStatus.FAILING
        ):
            _notify_staff(resource, recovered=False)
        elif (
            previous_status == MonitoredResource.HealthStatus.FAILING
            and resource.health_status == MonitoredResource.HealthStatus.HEALTHY
        ):
            _notify_staff(resource, recovered=True)

    return HealthCheckSummary(checked=checked, healthy=healthy, failing=failing)


def _check_resource(resource: MonitoredResource, timeout: int) -> None:
    api_key = resource.get_api_key()
    headers = {}
    if not isinstance(resource.scraping_parameters, dict):
        raise ValueError(
            f"Resource {resource.pk} scraping_parameters must be a JSON object."
        )
    params = resource.scraping_parameters.get("health_check_params", {})
    if not isinstance(params, dict):
        raise ValueError(
            f"Resource {resource.pk} health_check_params must be a JSON object."
        )

    if api_key:
        value = f"{resource.credential_prefix}{api_key}"
        if resource.credential_location == MonitoredResource.CredentialLocation.HEADER:
            if not resource.credential_name:
                raise ValueError(
                    f"Resource {resource.pk} requires a credential header name."
                )
            headers[resource.credential_name] = value
        else:
            if not resource.credential_name:
                raise ValueError(
                    f"Resource {resource.pk} requires a credential query name."
                )
            params = {**params, resource.credential_name: value}

    response = requests.get(
        resource.url,
        headers=headers,
        params=params,
        timeout=timeout,
        allow_redirects=False,
    )
    if not 200 <= response.status_code < 400:
        raise requests.HTTPError(
            f"HTTP {response.status_code} returned by monitored resource."
        )


def _notify_staff(resource: MonitoredResource, *, recovered: bool) -> None:
    recipients = User.objects.filter(
        is_active=True,
        is_staff=True,
        fl_deleted=False,
    ).exclude(email="").values_list("email", flat=True)
    if recovered:
        subject = f"VisionAlert: resource recovered - {resource.name}"
        message = (
            f"The monitored resource {resource.name} is responding again.\n"
            f"URL: {resource.url}"
        )
    else:
        subject = f"VisionAlert: resource failing - {resource.name}"
        message = (
            f"The monitored resource {resource.name} is failing its health check.\n"
            f"URL: {resource.url}\n"
            f"Error: {resource.last_error}"
        )

    for email in recipients:
        try:
            sent = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except (OSError, smtplib.SMTPException):
            logger.exception(
                "Could not notify staff about resource %s",
                resource.pk,
            )
            continue
        if sent != 1:
            logger.error(
                "Email backend did not notify staff about resource %s",
                resource.pk,
            )


def _safe_error_message(error: requests.RequestException, api_key: str) -> str:
    message = str(error)
    if api_key:
        message = message.replace(api_key, "[redacted]")
    return message[:1000]
