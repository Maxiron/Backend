# django_rest_framework imports
from rest_framework.serializers import ModelSerializer, CharField
# App imports
from Accounts.models import CustomUser


class CustomUserSerializer(ModelSerializer):
    # full_name is from the get_full_name method in the CustomUser model
    full_name = CharField(source="get_full_name", read_only=True)
    class Meta:
        model = CustomUser
        fields = [
            "full_name",
            "level",
            "matric_no",
            "is_verified",
        ]
        read_only_fields = ["email", "phone", "matric_no", "is_verified"]

        # If is_verified is True, return Success, else return Failure
        def to_representation(self, instance):
            data = super().to_representation(instance)
            if instance.is_verified:
                data["is_verified"] = "Verified"
            else:
                data["is_verified"] = "Not Verified"
            return data
        