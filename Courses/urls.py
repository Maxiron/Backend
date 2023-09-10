# Django imports
from django.urls import path

# Own imports
from .views import *


urlpatterns = [
    path('add-course/', AddCourseAPIView.as_view(), name="add-course"),
    path('list-course/', ListCourseAPIView.as_view(), name="list-course"),
    path('register-course/', RegisterCourseAPIView.as_view(), name="register-course"),
    path('list-registered-course/', ListRegisteredCourseAPIView.as_view(), name="list-registered-course"),
    path('filter-course/', ListCourseBySemesterAndLevelAPIView.as_view(), name="filter-course"),
    path('course-dashboard/', CourseDashboardAPIView.as_view(), name="course-dashboard"),
]