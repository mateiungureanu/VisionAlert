import re
from rest_framework import serializers
from .models import User


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