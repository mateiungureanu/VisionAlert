from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import DeleteAccountView, LoginView, RegisterView, MeView, BrandListView, BrandSubscriptionListCreateView, BrandSubscriptionDeleteView

urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('auth/me/', MeView.as_view()),
    path('auth/me/delete/', DeleteAccountView.as_view(), name='delete-account'),
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('subscriptions/', BrandSubscriptionListCreateView.as_view(), name='brand-subscription-list'),
    path('subscriptions/<int:brand_id>/', BrandSubscriptionDeleteView.as_view(), name='brand-subscription-delete')
]