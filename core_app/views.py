from django.shortcuts import render

# Create your views here.
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import BrandSubscriptionFavoriteSerializer, LoginSerializer, RegisterSerializer, UserSerializer, BrandSerializer, CategoryOptionSerializer, BrandSubscriptionSerializer, BrandSubscriptionWriteSerializer, OfferSerializer
from .models import Brand, BrandSubscription, Offer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class DeleteAccountView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def delete(self, request):
        user = request.user
        user.first_name = ''
        user.last_name = ''
        user.username = f'deleted-{user.pk}'
        user.email = f'deleted-{user.pk}@deleted.invalid'
        user.phone = None
        user.set_unusable_password()
        user.is_active = False
        user.fl_deleted = True
        user.save(update_fields=[
            'first_name',
            'last_name',
            'username',
            'email',
            'phone',
            'password',
            'is_active',
            'fl_deleted',
        ])
        return Response(status=status.HTTP_204_NO_CONTENT)


class BrandListView(generics.ListAPIView):
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Brand.objects.filter(fl_disabled=False).prefetch_related('categories')
    

class BrandSubscriptionListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscriptions = (
            request.user.brand_subscriptions
            .select_related('brand')
            .prefetch_related('categories')
        )
        return Response(BrandSubscriptionSerializer(subscriptions, many=True).data)

    def post(self, request):
        serializer = BrandSubscriptionWriteSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        brand = serializer.validated_data['brand']
        is_subscribed = request.user.brand_subscriptions.filter(brand=brand).exists()
        subscription = serializer.save()
        return Response(
            BrandSubscriptionSerializer(subscription).data,
            status=status.HTTP_200_OK if is_subscribed else status.HTTP_201_CREATED,
        )


class BrandSubscriptionDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, brand_id):
        subscription = get_object_or_404(
            BrandSubscription,
            user=request.user,
            brand_id=brand_id,
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BrandSubscriptionFavoriteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, brand_id):
        subscription = get_object_or_404(
            BrandSubscription.objects.select_related('brand').prefetch_related('categories'),
            user=request.user,
            brand_id=brand_id,
        )
        serializer = BrandSubscriptionFavoriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription.is_favorite = serializer.validated_data['is_favorite']
        subscription.save(update_fields=['is_favorite'])
        return Response(BrandSubscriptionSerializer(subscription).data)


def matched_offers(user, favorites_only=False):
    subscriptions = (
        BrandSubscription.objects.filter(user=user, brand__fl_disabled=False)
        .prefetch_related('categories')
    )
    if favorites_only:
        subscriptions = subscriptions.filter(is_favorite=True)

    subscription_filters = Q(pk__in=[])
    for subscription in subscriptions:
        category_ids = [
            category.id
            for category in subscription.categories.all()
            if not category.fl_disabled
        ]
        subscription_filter = Q(brand_id=subscription.brand_id)
        if category_ids:
            subscription_filter &= (
                Q(categories__id__in=category_ids)
                | Q(categories__isnull=True)
            )
        subscription_filters |= subscription_filter

    return (
        Offer.objects.filter(subscription_filters)
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.now()))
        .distinct()
        .select_related('brand')
        .prefetch_related('categories', 'sources')
        .order_by('-created_at', '-id')
    )


class MyOffersView(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return matched_offers(self.request.user)


class FavoriteOffersPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


NO_DISCOUNT = 'none'
DISCOUNT_BAND_SIZE = 10
DISCOUNT_TOP_BAND = 50  # the last band is open-ended: 50% or more


def discount_band(value):
    """Band key for a discount: '0', '10', ..., '50' (50 and above) or 'none'."""
    if value is None:
        return NO_DISCOUNT
    band = int(value // DISCOUNT_BAND_SIZE) * DISCOUNT_BAND_SIZE
    return str(min(max(band, 0), DISCOUNT_TOP_BAND))


def discount_band_filter(key):
    if key == NO_DISCOUNT:
        return Q(discount_percentage__isnull=True)
    if not key.isdigit():
        return None
    start = int(key)
    if start % DISCOUNT_BAND_SIZE or start > DISCOUNT_TOP_BAND:
        return None
    band_filter = Q(discount_percentage__gte=start)
    if start == 0:
        band_filter = Q(discount_percentage__lt=DISCOUNT_BAND_SIZE)
    elif start < DISCOUNT_TOP_BAND:
        band_filter &= Q(discount_percentage__lt=start + DISCOUNT_BAND_SIZE)
    return band_filter


def favorite_offers(request, apply_discounts=True):
    """Favorite-brand offers narrowed by ?brands=, ?search= and ?discounts=."""
    queryset = matched_offers(request.user, favorites_only=True)
    params = request.query_params

    raw_brands = params.get('brands', '')
    brand_ids = [int(value) for value in raw_brands.split(',') if value.strip().isdigit()]
    if raw_brands and not brand_ids:
        return queryset.none()
    if brand_ids:
        queryset = queryset.filter(brand_id__in=brand_ids)

    search = params.get('search', '').strip()
    if search:
        queryset = queryset.filter(title__icontains=search)

    raw_discounts = params.get('discounts', '')
    if apply_discounts and raw_discounts:
        band_filters = [
            band_filter
            for band_filter in (
                discount_band_filter(key.strip()) for key in raw_discounts.split(',')
            )
            if band_filter is not None
        ]
        if not band_filters:
            return queryset.none()
        combined = band_filters[0]
        for band_filter in band_filters[1:]:
            combined |= band_filter
        queryset = queryset.filter(combined)
    return queryset


class FavoriteOffersView(generics.ListAPIView):
    """Paginated offers from the user's favorite brands.

    Optional filters: ?brands=1,3 narrows the result to those brand ids,
    ?search=text keeps only offers whose title contains the text and
    ?discounts=10,20,none keeps offers in those discount bands.
    """
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = FavoriteOffersPagination

    def get_queryset(self):
        return favorite_offers(self.request)


class FavoriteOfferDiscountsView(APIView):
    """Discount bands that exist among the favorite offers, with offer counts.

    Honors ?brands= and ?search= but not ?discounts=, so every band stays
    selectable while others are already chosen.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        counts = {}
        for _, discount in favorite_offers(request, apply_discounts=False).values_list(
            'id', 'discount_percentage'
        ):
            key = discount_band(discount)
            counts[key] = counts.get(key, 0) + 1
        bands = sorted(
            (key for key in counts if key != NO_DISCOUNT), key=int
        )
        if NO_DISCOUNT in counts:
            bands.append(NO_DISCOUNT)
        return Response([{'key': key, 'count': counts[key]} for key in bands])