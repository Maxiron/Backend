# rest_framework imports
from rest_framework import serializers

# Django imports

# App imports
from .models import Course, RegisteredCourse


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'title', 'code', 'level', 'semester', 'unit', 'date_created')
        read_only_fields = ('id', 'date_created')

class RegisteredCourseSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    student = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = RegisteredCourse
        fields = ('course', 'student', 'date_created')
        read_only_fields = ('id', 'date_created')