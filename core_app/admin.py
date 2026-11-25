from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from core_app.models import (
    Brand,
    BrandSubscription,
    Category,
    MonitoredResource,
    SocialMediaPlatform,
    User,
)


class MonitoredResourceAdminForm(forms.ModelForm):
    api_key = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Leave blank to keep the current key.",
    )
    clear_api_key = forms.BooleanField(
        required=False,
        label="Remove stored API key",
    )

    class Meta:
        model = MonitoredResource
        exclude = ("api_key_encrypted",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.api_key_encrypted:
            self.fields["api_key"].help_text = (
                "A key is stored. Leave blank to keep it."
            )

    def clean(self):
        cleaned_data = super().clean()
        api_key = cleaned_data.get("api_key")
        if api_key and not cleaned_data.get("clear_api_key"):
            try:
                self.instance.set_api_key(api_key)
            except ImproperlyConfigured as error:
                self.add_error("api_key", str(error))
        return cleaned_data

    def clean_scraping_parameters(self):
        parameters = self.cleaned_data["scraping_parameters"]
        if not isinstance(parameters, dict):
            raise forms.ValidationError(
                "Scraping parameters must be a JSON object."
            )
        return parameters

    def save(self, commit=True):
        resource = super().save(commit=False)
        api_key = self.cleaned_data["api_key"]
        if self.cleaned_data["clear_api_key"]:
            resource.set_api_key("")
        elif api_key:
            resource.set_api_key(api_key)
        if commit:
            resource.save()
            self.save_m2m()
        return resource


@admin.register(MonitoredResource)
class MonitoredResourceAdmin(admin.ModelAdmin):
    form = MonitoredResourceAdminForm
    list_display = (
        "name",
        "resource_type",
        "brand",
        "enabled",
        "health_status",
        "last_checked_at",
    )
    list_filter = ("resource_type", "enabled", "health_status")
    search_fields = ("name", "url", "brand__name")
    readonly_fields = ("health_status", "last_checked_at", "last_error")
    fieldsets = (
        (
            "Resource",
            {
                "fields": (
                    "name",
                    "brand",
                    "resource_type",
                    "url",
                    "enabled",
                    "scraping_parameters",
                )
            },
        ),
        (
            "API credentials",
            {
                "fields": (
                    "credential_location",
                    "credential_name",
                    "credential_prefix",
                    "api_key",
                    "clear_api_key",
                )
            },
        ),
        (
            "Health",
            {
                "fields": ("health_status", "last_checked_at", "last_error"),
            },
        ),
    )


admin.site.register(User, UserAdmin)
admin.site.register(Category)
admin.site.register(SocialMediaPlatform)
admin.site.register(BrandSubscription)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        MonitoredResource.objects.get_or_create(
            brand=obj,
            resource_type=MonitoredResource.ResourceType.WEBSITE,
            defaults={
                "name": obj.name,
                "url": obj.official_website,
                "enabled": not obj.fl_disabled,
            },
        )