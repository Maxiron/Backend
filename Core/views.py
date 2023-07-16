# Author: Nwokoro Aaron Nnamdi
# Date created: Thursday, 29th June 2023

# Python imports

# Third party imports
from cloudinary.uploader import destroy

# Django imports
from django.conf import settings
from django.shortcuts import render
from django.db.models import Q

# rest_framework imports
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

# App imports
from Accounts.models import CustomUser

# Own imports
from .serializers import CustomUserSerializer

def index(request):
    return render(request, "index.html")


class CustomPagination(PageNumberPagination):
    page_size = 10

class AdminHomeAnalyticsAPIVIew(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Get total students, total verified students and total unverified students
        total_students = CustomUser.objects.filter(is_staff=False).count()
        total_verified_students = CustomUser.objects.filter(is_staff=False, is_verified=True).count()
        total_unverified_students = CustomUser.objects.filter(is_staff=False, is_verified=False).count()

        response = {
            "message": "Success",
            "data": {
                "total_students": total_students,
                "total_verified_students": total_verified_students,
                "total_unverified_students": total_unverified_students,
            }            
        }

        return Response(response, status=status.HTTP_200_OK)
    


class AdminStudentsAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        # Get query parameters
        search_name = self.request.query_params.get('name', None)
        filter_level = self.request.query_params.get('level', None)
        filter_is_verified = self.request.query_params.get('status', None)

        # Filter students
        queryset = CustomUser.objects.filter(is_staff=False).order_by("first_name")

        if search_name:
            # Add search by name
            queryset = queryset.filter(Q(first_name__icontains=search_name) | Q(last_name__icontains=search_name) | Q(middle_name__icontains=search_name))

        if filter_level:
            # Filter by level
            queryset = queryset.filter(level=filter_level)

        if filter_is_verified:
            # Filter by is_verified
            # accepts verified or unverified
            if filter_is_verified == "verified":
                filter_is_verified = True
            elif filter_is_verified == "unverified":
                filter_is_verified = False
            else:
                filter_is_verified = True
            queryset = queryset.filter(is_verified=filter_is_verified)

        return queryset


