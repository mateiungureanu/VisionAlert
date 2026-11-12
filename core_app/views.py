from django.shortcuts import render

# Create your views here.
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer, BrandSerializer, CategoryOptionSerializer, BrandSubscriptionSerializer, BrandSubscriptionWriteSerializer, OfferSerializer
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


class MyOffersView(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        subscriptions = (
            BrandSubscription.objects.filter(
                user=self.request.user,
                brand__fl_disabled=False,
            )
            .prefetch_related('categories')
        )
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