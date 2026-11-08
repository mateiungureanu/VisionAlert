from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, URLValidator
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


class Offer(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='offers')
    categories = models.ManyToManyField(Category, blank=True, related_name='offers')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand.name} - {self.title}"
    

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
