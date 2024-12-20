# Django imports
from django.urls import path

# Own imports
from .views import AdminHomeAnalyticsAPIVIew, AdminStudentsAPIView

urlpatterns = [
    path("students/analytics/", AdminHomeAnalyticsAPIVIew.as_view(), name="students-analytics"),
    path("students/", AdminStudentsAPIView.as_view(), name="students"),
]