# Author: Nwokoro Aaron Nnamdi
# Date created: Thursday, 29th June 2023

# django imports
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import (
    smart_str,
    force_str,
)
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

# rest_framework imports
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

# App imports
from .models import CustomUser, FaceEmbedding



class RegistrationSerializer(serializers.ModelSerializer):
    """Serializes registration requests and creates a new user."""

    # Ensure passwords are at least 8 characters long, no longer than 128
    # characters, and can not be read by the client.
    password = serializers.CharField(max_length=128, min_length=8, write_only=True)

    class Meta:
        model = CustomUser
        # List all of the fields that could possibly be included in a request
        # or response, including fields specified explicitly above.
        fields = [
            "email",
            "phone",
            "password",
            "first_name",
            "last_name",
            "level",
            "matric_no",
        ] 

    def create(self, validated_data):
        # Use the `create_user` method we wrote earlier to create a new user.
        return CustomUser.objects.create_user(**validated_data)
      



class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = CustomUser
        fields = ("email", "password")


class UpdateUserSerializer(serializers.ModelSerializer):
    """Handles serialization and deserialization of User objects."""

    password = serializers.CharField(max_length=128, min_length=6, write_only=True)
    profile_picture_url = serializers.ReadOnlyField()

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "phone",
            "password",
            "first_name",
            "middle_name",
            "last_name",
            "profile_picture",
            "profile_picture_url",
            "is_active",
            "level",
            "matric_no",
            "is_verified",
            "is_staff",            
        )
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop("profile_picture")
        return representation  

class ChangePasswordSerializer(serializers.Serializer):
    model = CustomUser

    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class PasswordResetRequestEmailViewSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)
    redirect_url = serializers.CharField(max_length=500, required=False)

    class Meta:
        fields = ["email"]


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uidb64 = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        fields = ["password", "token", "uidb64"]

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            token = attrs.get("token")
            uidb64 = attrs.get("uidb64")

            id = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed("The reset link is invalid", 401)

            user.set_password(password)
            user.save()

            return user
        except Exception as e:
            raise AuthenticationFailed("The reset link is invalid", 401)
        return super().validate(attrs)

class FaceEmbeddingSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = FaceEmbedding
        fields = ('id', 'user', 'embedding')