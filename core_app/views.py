from django.shortcuts import render

# Create your views here.
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


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