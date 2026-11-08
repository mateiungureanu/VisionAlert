import re
from django.contrib.auth import authenticate
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User, Brand, Category, BrandSubscription


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone', 'password']
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Există deja un cont cu acest email.')
        return value

    def validate_password(self, value):
        errors = []
        if not 8 <= len(value) <= 64:
            errors.append('Parola trebuie să aibă între 8 și 64 de caractere.')
        if not re.search(r'[A-Z]', value):
            errors.append('Parola trebuie să conțină o literă mare.')
        if not re.search(r'\d', value):
            errors.append('Parola trebuie să conțină o cifră.')
        if not re.search(r'[^A-Za-z0-9]', value):
            errors.append('Parola trebuie să conțină un caracter special.')
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def create(self, validated_data):
        # create_user hashuiește parola automat (PBKDF2)
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'phone', 'date_joined']


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs['identifier'].strip()
        user = User.objects.filter(email__iexact=identifier).first()
        if user is None:
            user = User.objects.filter(username__iexact=identifier).first()

        authenticated_user = authenticate(
            request=self.context.get('request'),
            email=user.email if user else identifier,
            password=attrs['password'],
        )
        if authenticated_user is None:
            raise AuthenticationFailed('Nu există un cont cu aceste date de autentificare.')

        refresh = TokenObtainPairSerializer.get_token(authenticated_user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class CategoryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class BrandSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    official_website = serializers.URLField(read_only=True)
    categories = serializers.SerializerMethodField()

    def get_categories(self, brand):
        categories = brand.categories.filter(fl_disabled=False)
        return CategoryOptionSerializer(categories, many=True).data 


class BrandSubscriptionSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    categories = CategoryOptionSerializer(many=True, read_only=True)

    class Meta:
        model = BrandSubscription
        fields = ['id', 'brand', 'categories', 'created_at']


class BrandSubscriptionWriteSerializer(serializers.Serializer):
    brand_id = serializers.PrimaryKeyRelatedField(
        source='brand', 
        queryset=Brand.objects.filter(fl_disabled=False)
    )
    category_ids = serializers.PrimaryKeyRelatedField(
        source='categories', 
        queryset=Category.objects.filter(fl_disabled=False), 
        many=True, 
        required=False
    )

    def validate(self, attrs):
        brand = attrs['brand']
        categories = attrs.get('categories', [])
        if any(category.brand_id != brand.id for category in categories):
            raise serializers.ValidationError(
                {'category_ids': 'Toate categoriile trebuie să aparțină brandului selectat.'}
            )
        return attrs

    def create(self, validated_data):
        categories = validated_data.get('categories', [])
        subscription, _ = BrandSubscription.objects.get_or_create(
            user=self.context['request'].user, 
            brand=validated_data['brand']
        )
        subscription.categories.set(categories)
        return subscription