from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from .models import Brand, BrandSubscription, Category, SocialMediaPlatform, User

admin.site.register(User, UserAdmin)
admin.site.register(Brand)
admin.site.register(Category)
admin.site.register(SocialMediaPlatform)
admin.site.register(BrandSubscription)