# django_rest_framework imports
from rest_framework.serializers import ModelSerializer, CharField
# App imports
from Accounts.models import CustomUser


class CustomUserSerializer(ModelSerializer):
    # full_name is from the get_full_name method in the CustomUser model
    full_name = CharField(source="get_full_name", read_only=True)
    # Change is_verified to a status
    status = CharField(source="is_verified", read_only=True)
    class Meta:
        model = CustomUser
        fields = [
            "full_name",
            "level",
            "option",
            "matric_no",
            "status",
        ]
        read_only_fields = fields