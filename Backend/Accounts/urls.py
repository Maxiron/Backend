from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegistrationAPIView,
    LoginAPIView,
    LogoutAPIView,
    UserRetrieveUpdateAPIView,
    ChangePasswordView,
)
from .face import RegisterFaceAPIView, RecognizeCheckAPIView

urlpatterns = [
    path("register/", RegistrationAPIView.as_view(), name="register"),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("user/", UserRetrieveUpdateAPIView.as_view(), name="user"),
    path("password/change/", ChangePasswordView.as_view(), name="change-password"),

    path("face/register/", RegisterFaceAPIView.as_view(), name="register-face"),
    path("face/verify/", RecognizeCheckAPIView.as_view(), name="verify-face-check"),

    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]