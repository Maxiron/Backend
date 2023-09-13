# Author: Nwokoro Aaron Nnamdi
# Date created: Thursday, 29th June 2023

# Python imports

# Third party imports

# Django imports
from django.conf import settings
from django.shortcuts import render

# rest_framework imports
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

# App imports
from .models import Course, RegisteredCourse
from .serializers import CourseSerializer, RegisteredCourseSerializer


# API to add courses from Admin Section
class AddCourseAPIView(APIView):
    permission_classes = (IsAdminUser,)
    serializer_class = CourseSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        course_data = serializer.data
        response = {
            'data': {
                'status': 'success',
                'course': dict(course_data),
                'message': 'Course added successfully'
            }
        }
        return Response(response, status=status.HTTP_201_CREATED)
    

# API to list courses from Admin Section
class ListCourseAPIView(ListAPIView):
    permission_classes = (IsAdminUser,)
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    pagination_class = PageNumberPagination


# API to Register Courses from the Student Section
class RegisterCourseAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RegisteredCourseSerializer

    def post(self, request):
        # Get the student
        student = request.user
        # Get the course
        course_ids = request.data.get('course_ids', [])

        total_units = 0

        # Create a list for the courses that have been registered
        registered_courses = []

        for course_id in course_ids:
            try:
                course = Course.objects.get(id=course_id)

                # Check if the student has registered for the course before
                if RegisteredCourse.objects.filter(student=student, course=course).exists():
                    response = {
                        'status': 'error',
                        'message': f'You have already registered for {course.title}'
                    }
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)

                # Add the course to the list of registered courses
                registered_courses.append(course)

                total_units += course.unit
            except Course.DoesNotExist:
                response = {
                    'status': 'error',
                    'message': f'Course with id {course_id} does not exist.'
                    }
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

        # Check if the student has registered for the maximum number of units allowed
        if total_units > 27:
            response = {
                'data': {
                    'status': 'error',
                    'message': 'You have exceeded the maximum number of units allowed'
                }
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        print(len(registered_courses))

        # Iterate over the registered courses list and create new objects
        new_registered_courses = [
            RegisteredCourse(
                student=student,
                course=course
            )
            for course in registered_courses
        ]

        # Bulk create the new registered courses
        RegisteredCourse.objects.bulk_create(new_registered_courses)
        response = {
            'data': {
                'status': 'success',
                'message': 'Course registered successfully'
            }
        }

        return Response(response, status=status.HTTP_201_CREATED)
        

# API to list registered courses from the Student Section
class ListRegisteredCourseAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RegisteredCourseSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        student = self.request.user
        return RegisteredCourse.objects.filter(student=student)


# API to list courses based on semester and Level filter
class ListCourseBySemesterAndLevelAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = CourseSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        level = self.request.query_params.get('level', None)
        semester = self.request.query_params.get('semester', None)
        return Course.objects.filter(level=level, semester=semester)
    

# Course Dashboard API
# API to list courses registered in all semesters by a student
# API to list courses registered in the current session by a student
# API to list total number of units registered in all semesters by a student
class CourseDashboardAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        student = request.user
        response = {
            'data': {
                'status': 'success',
                'courses': RegisteredCourseSerializer(RegisteredCourse.objects.filter(student=student), many=True).data,
                'total_units': RegisteredCourse.get_total_units(student),
                'total_courses': RegisteredCourse.get_total_courses(student),
                'total_courses_current_semester': RegisteredCourse.get_total_courses_current_semester(student), 
            }
        }
        return Response(response, status=status.HTTP_200_OK)

