# Description: Contains the models for the Courses app

# Python imports
from datetime import datetime

# Django imports
from django.db import models

# Own imports
from Accounts.models import CustomUser


# Contains all the courses offered in the dept
class Course(models.Model):
    code = models.CharField(max_length=10, unique=True, help_text="Course code")
    title = models.CharField(max_length=100, help_text="Course title")
    unit = models.IntegerField(help_text="Course unit")
    level = models.IntegerField(help_text="Level which the course is offered")

    semester_choices = (
        ("Hamattan", "Harmattan"),
        ("Rain", "Rain"),
    )
    semester = models.CharField(
        max_length=10, choices=semester_choices, 
        help_text="Semester which the course is offered"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code
    
    class Meta:
        ordering = ["-level"]
        verbose_name_plural = "Courses"

# Holds all the courses a student has registered for
class RegisteredCourse(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.course}"
    
    class Meta:
        ordering = ["-date_created"]
        verbose_name_plural = "Registered Courses"

    # Function to get the total number of units a student has registered for
    @staticmethod
    def get_total_units(student):
        total_units = 0
        for course in RegisteredCourse.objects.filter(student=student):
            total_units += course.course.unit
        return total_units
    
    # Function to get the total number of courses a student has registered for
    @staticmethod
    def get_total_courses(student):
        return RegisteredCourse.objects.filter(student=student).count()
        
    # Function to get the current semester
    @staticmethod
    def get_current_semester():
        # If the current year is the year of the last registered course, return the semester of the last registered course
        if RegisteredCourse.objects.last().date_created.year == datetime.now().year:
            return RegisteredCourse.objects.last().course.semester
        else:
            return "Harmattan"
    
    # Function to get the total number of courses a student has registered for in the current semester
    @staticmethod
    def get_total_courses_current_semester(student):
        # Get the current semester
        current_semester = RegisteredCourse.get_current_semester()
        # Get the total number of courses registered by the student in the current semester
        return RegisteredCourse.objects.filter(student=student, course__semester=current_semester).count()
    
        



