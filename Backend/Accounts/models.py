# Author: Nwokoro Aaron Nnamdi
# Date created: Thursday, 29th June 2023

# Description: This file contains the model for the user.

# Python imports
import uuid
import os

# Django imports
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

# Third party imports
import numpy as np
from cloudinary.models import CloudinaryField
from decouple import config


class UserManager(BaseUserManager):
    """
    Django requires that custom users define their own Manager class. By
    inheriting from `BaseUserManager`, we get a lot of the same functionalities
    used by Django to create a `User`.

    All we have to do is override the `create_user` function which we will use
    to create `User` objects.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a `User` with an email and password."""

        if email is None:
            raise TypeError("Users must have an email address.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, password):
        """
        Create and return a `User` with superuser (admin) permissions.
        """

        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.is_verified = True
        user.is_active = True
        user.save()

        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(db_index=True, unique=True, null=False)

    phone = models.CharField(max_length=20, unique=True, null=False)

    first_name = models.CharField(max_length=120, null=False)

    middle_name = models.CharField(max_length=120, null=True)

    last_name = models.CharField(max_length=120, null=False)

    # Choice Field (100, 200, 300, 400, 500)
    LEVEL_CHOICES = (
        ("100", "100"),
        ("200", "200"),
        ("300", "300"),
        ("400", "400"),
        ("500", "500"),
    )
    level = models.CharField(max_length=3, choices=LEVEL_CHOICES, null=False)

    matric_no = models.CharField(max_length=20, unique=True, null=False)

    # This field is used to determine if the user has verified his/her face
    is_verified = models.BooleanField(default=False)

    # This field will be used to store the users profile picture using cloudinary
    profile_picture = CloudinaryField('image', blank=True, null=True)

    # Users will be able to deactivate their account when this is False
    is_active = models.BooleanField(default=False)

    # This is used to determine who can log into the Django admin
    is_staff = models.BooleanField(default=False)

    # A timestamp representing when this object was created.
    created_at = models.DateTimeField(auto_now_add=True)

    # A timestamp reprensenting when this object was last updated.
    updated_at = models.DateTimeField(auto_now=True)

    # The `USERNAME_FIELD` property tells us which field we will use to log in.
    # In this case we want it to be the email field.
    USERNAME_FIELD = "email"
    # REQUIRED_FIELDS = []

    # Tells Django that the UserManager class defined above should manage
    # objects of this type.
    objects = UserManager()

    class Meta:
        managed = True

    def __str__(self) -> str:
        # Returns a string representation of this User
        return self.email
    
    @property
    def profile_picture_url(self):
        # If picture is None
        if not self.profile_picture:
            return (
                "https://res.cloudinary.com/dxyyxfosd/pyzjrq7bnywos6r9thpp"
            )
        return (
                f"https://res.cloudinary.com/{config('CLOUDINARY_CLOUD_NAME')}/{self.profile_picture}"
            )
    

# Define the Django models for storing the face embeddings and names
class FaceEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=False)
    embedding = models.BinaryField(
        help_text="binary field to store the face embeddings as bytes"
        )
    
    # This method is used to convert the numpy array to bytes
    def set_embedding(self, embedding):
        self.embedding = embedding.tobytes()
    
    # This method is used to convert the bytes back to a numpy array.
    def get_embedding(self):
        return np.frombuffer(self.embedding)

    def __str__(self):
        return self.user.email

    class Meta:
        verbose_name_plural = "Face embeddings"
    
