from cryptography.fernet import Fernet, InvalidToken

from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
    URLValidator,
)
from django.db import models
from django.db.models.functions import Lower

# Create your models here.
class User(AbstractUser):
    # AbstractUser are deja: id, username, first_name, last_name, email, password
    email = models.EmailField(unique=True)
    fl_deleted = models.BooleanField(default=False)
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?[0-9]{9,15}$', 'Număr de telefon invalid.')],
    )



    USERNAME_FIELD = 'email'  # login se face cu email
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

class Brand(models.Model):
    name = models.CharField(max_length=100)
    official_website = models.URLField(blank=False, null=False)
    fl_disabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(Lower('name'), name='unique_brand_name_ci'),
            models.UniqueConstraint(Lower('official_website'), name='unique_brand_official_website_ci'),
        ]

    def __str__(self):
        return self.name


class Category(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    url = models.URLField(blank=True, null=True, validators=[URLValidator(schemes=['http', 'https'])])
    fl_disabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint('brand', Lower('name'), name='unique_category_name_ci'),
            models.UniqueConstraint('brand', Lower('url'), name='unique_category_url_ci'),
        ]
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class BrandSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='brand_subscriptions')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='subscriptions')
    categories = models.ManyToManyField(Category, blank=True, related_name='subscriptions')
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'brand'], name='unique_user_brand_subscription'),
        ]

    def __str__(self):
        return f"{self.user} - {self.brand}"
    

class SocialMediaPlatform(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='social_media_platforms')
    name = models.CharField(max_length=100)
    url = models.URLField(blank=False, null=False, validators=[URLValidator(schemes=['http', 'https'])])
    fl_disabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint('brand', Lower('name'), name='unique_social_media_platform_name_ci'),
            models.UniqueConstraint('brand', Lower('url'), name='unique_social_media_platform_url_ci'),
        ]

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class MonitoredResource(models.Model):
    class ResourceType(models.TextChoices):
        WEBSITE = "website", "Website"
        API = "api", "API"

    class CredentialLocation(models.TextChoices):
        HEADER = "header", "HTTP header"
        QUERY = "query", "Query parameter"

    class HealthStatus(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        HEALTHY = "healthy", "Healthy"
        FAILING = "failing", "Failing"

    name = models.CharField(max_length=150)
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="monitored_resources",
    )
    resource_type = models.CharField(
        max_length=10,
        choices=ResourceType.choices,
        default=ResourceType.WEBSITE,
    )
    url = models.URLField(validators=[URLValidator(schemes=["http", "https"])])
    enabled = models.BooleanField(default=True)
    scraping_parameters = models.JSONField(default=dict, blank=True)
    credential_location = models.CharField(
        max_length=10,
        choices=CredentialLocation.choices,
        default=CredentialLocation.HEADER,
    )
    credential_name = models.CharField(
        max_length=100,
        blank=True,
        default="Authorization",
    )
    credential_prefix = models.CharField(max_length=100, blank=True, default="Bearer ")
    api_key_encrypted = models.TextField(blank=True, editable=False)
    health_status = models.CharField(
        max_length=10,
        choices=HealthStatus.choices,
        default=HealthStatus.UNKNOWN,
    )
    last_checked_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_api_key(self, api_key: str) -> None:
        if not api_key:
            self.api_key_encrypted = ""
            return
        key = getattr(settings, "RESOURCE_CREDENTIAL_ENCRYPTION_KEY", "")
        if not key:
            raise ImproperlyConfigured(
                "RESOURCE_CREDENTIAL_ENCRYPTION_KEY must be configured "
                "before saving API keys."
            )
        try:
            self.api_key_encrypted = Fernet(key.encode("ascii")).encrypt(
                api_key.encode("utf-8")
            ).decode("ascii")
        except (ValueError, UnicodeEncodeError) as exc:
            raise ImproperlyConfigured(
                "RESOURCE_CREDENTIAL_ENCRYPTION_KEY must be a valid Fernet key."
            ) from exc

    def get_api_key(self) -> str:
        if not self.api_key_encrypted:
            return ""
        key = getattr(settings, "RESOURCE_CREDENTIAL_ENCRYPTION_KEY", "")
        if not key:
            raise ImproperlyConfigured(
                "RESOURCE_CREDENTIAL_ENCRYPTION_KEY must be configured "
                "before using API keys."
            )
        try:
            return Fernet(key.encode("ascii")).decrypt(
                self.api_key_encrypted.encode("ascii")
            ).decode("utf-8")
        except (InvalidToken, ValueError, UnicodeEncodeError) as exc:
            raise ImproperlyConfigured(
                "Could not decrypt a monitored resource API key; verify "
                "RESOURCE_CREDENTIAL_ENCRYPTION_KEY."
            ) from exc


class Offer(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='offers')
    categories = models.ManyToManyField(Category, blank=True, related_name='offers')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    products = models.JSONField(default=list, blank=True)
    terms = models.TextField(blank=True)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    previous_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand.name} - {self.title}"
    

class FavoriteOffer(models.Model):
    """Association table: a user can favorite many offers, an offer can be favorited by many users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_offers')
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'offer'], name='unique_user_favorite_offer'),
        ]

    def __str__(self):
        return f"{self.user} - {self.offer}"


class OfferSource(models.Model):
    class SourceType(models.TextChoices):
        WEBSITE = "website", "Website"
        SOCIAL = "social", "Social"

    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="sources")
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    url = models.URLField()
    social_account = models.ForeignKey(
        SocialMediaPlatform,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="offer_sources",
    )
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["offer", "url"], name="unique_offer_source_url")
        ]
