from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import DeleteAccountView, LoginView, RegisterView, MeView, BrandListView, BrandSubscriptionListCreateView, BrandSubscriptionDeleteView, BrandSubscriptionFavoriteView, FavoriteOfferBrandsView, FavoriteOfferDiscountBandsView, FavoriteOfferDiscountsView, FavoriteOfferListView, FavoriteOfferToggleView, FavoriteOffersView, MyOffersView

urlpatterns = [
    path('auth/register/', RegisterView.as_view()),
    path('auth/login/', LoginView.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('auth/me/', MeView.as_view()),
    path('auth/me/delete/', DeleteAccountView.as_view(), name='delete-account'),
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('subscriptions/', BrandSubscriptionListCreateView.as_view(), name='brand-subscription-list'),
    path('subscriptions/<int:brand_id>/', BrandSubscriptionDeleteView.as_view(), name='brand-subscription-delete'),
    path('subscriptions/<int:brand_id>/favorite/', BrandSubscriptionFavoriteView.as_view(), name='brand-subscription-favorite'),
    path('offers/mine/', MyOffersView.as_view(), name='my-offers'),
    path('offers/favorites/', FavoriteOffersView.as_view(), name='favorite-offers'),
    path('offers/favorites/discounts/', FavoriteOfferDiscountsView.as_view(), name='favorite-offer-discounts'),
    path('favorite-offers/', FavoriteOfferListView.as_view(), name='favorite-offer-list'),
    path('favorite-offers/brands/', FavoriteOfferBrandsView.as_view(), name='favorite-offer-brand-facets'),
    path('favorite-offers/discounts/', FavoriteOfferDiscountBandsView.as_view(), name='favorite-offer-discount-facets'),
    path('favorite-offers/<int:offer_id>/', FavoriteOfferToggleView.as_view(), name='favorite-offer-toggle'),
]