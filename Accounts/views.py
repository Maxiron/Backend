# Author: Nwokoro Aaron Nnamdi
# Date created: Thursday, 29th June 2023

# Python imports

# Third party imports
from cloudinary.uploader import destroy

# Django imports
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponsePermanentRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import DjangoUnicodeDecodeError, force_bytes, smart_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

# rest_framework imports
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import (
    RefreshToken,
)

# Own imports
from .models import CustomUser
from .renderers import UserJSONRenderer
from .serializers import (
    ChangePasswordSerializer,
    PasswordResetRequestEmailViewSerializer,
    RegistrationSerializer,
    SetNewPasswordSerializer,
    UpdateUserSerializer,
    UserLoginSerializer,
)
from .utils import Util, EmailThread



class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = ["http", "https"]  # ,os.environ.get('APP_SCHEME')


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer
    renderer_classes = (UserJSONRenderer,)

    def post(self, request):

        # Get email from request
        email = request.data["email"]

        # Check if email is valid
        # if not Util.validate_email(email):
        #     response = {
        #         "status": False,
        #         "message": "Please use your valid school email address (@futo.edu.ng)",
        #     }
        #     return Response(response, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            response = {"status": "false", "message": serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
       
        # Save user to database
        user = serializer.save()
        user.is_active = True
        user.save()

        response = {
            "status": True,
            "email": email,
            "message": "User registered successfully. Proceed to Verify Face.",
        }
        return Response(response, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)  

    def post(self, request):
        try:
            serializer = UserLoginSerializer(data=request.data)

            if serializer.is_valid():
                email = request.data["email"]
                password = request.data["password"]

                user = authenticate(email=email, password=password)

                if not user:
                    # if user isn't authenticated
                    return Response(
                        {
                            "status": "false",
                            "message": "Invalid username or password",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # USER AUTHENTICATED 👇
                # If user is not verified
                if not user.is_verified:
                    return Response(
                        {
                            "status": "false",
                            "email": user.email,
                            "message": "Please verify your Face to continue",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # retrieve user details
                userdetails = UpdateUserSerializer(CustomUser.objects.get(id=user.id))

                tokens = RefreshToken.for_user(user)
                refresh = str(tokens)
                access = str(tokens.access_token)

                token_data = {"refresh": refresh, "access": access}

                response = {
                    "status": "true",
                    "token": token_data,
                    "userDetails": userdetails.data,
                }
                return Response(response, status=status.HTTP_200_OK)

            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()

                    # TODO
                    # set up a cron job on server which runs a command
                    # to delete blacklisted or expired tokens
                    return Response(status=status.HTTP_205_RESET_CONTENT)
                except Exception as e:
                    response = {"error": str(e)}
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            else:
                response = {"error": "Refresh token not provided"}
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(UpdateAPIView):
    # An endpoint for changing password.

    serializer_class = ChangePasswordSerializer
    model = CustomUser
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        try:
            self.user = self.request.user
            serializer = self.get_serializer(data=request.data)

            if serializer.is_valid():
                # Check old password
                if not self.user.check_password(serializer.data.get("old_password")):
                    return Response(
                        {"old_password": ["Wrong password."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # set_password also hashes the password that the user will get
                self.user.set_password(serializer.data.get("new_password"))
                self.user.save()
                response = {
                    "status": "success",
                    "message": "Password updated Successfully",
                }

                return Response(response, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestEmailView(GenericAPIView):
    serializer_class = PasswordResetRequestEmailViewSerializer

    def post(self, request):
        """
        params: email, redirect_url

                email: User's email
                redirect_url: Frontend url to redirect to password reset email sent page
        """

        serializer = self.serializer_class(data=request.data)
        email = request.data.get("email") or ""

        if CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request=request).domain # "127.0.0.1:8000"
            relativeLink = reverse(
                "reset-password-validate-token", kwargs={"uidb64": uidb64, "token": token}
            )

            redirect_url = request.data.get("redirect_url") or ""
            absurl = "http://" + current_site + relativeLink
            email_body = (
                "Hello, \n Use link below to reset your password  \n"
                + absurl
                + "?redirect_url="
                + redirect_url
            )
            # data = {'email_body': email_body, 'to_email': email,
            #         'email_subject': 'Reset your passsword'}
            message = render_to_string(
                "reset_password_email.html", {"email_body": email_body}
            )

            send_email = EmailMessage(
                subject="Reset your Password",
                body=message,
                to=[email],
            )
            send_email.content_subtype = "html"
            # send_email.send(fail_silently=True)
            EmailThread(send_email).start()
            print(send_email)
            print(message)

            response = {
                "status": "success",
                "message": "We have sent you a link to reset your password",
            }
            return Response(
                response,
                status=status.HTTP_200_OK,
            )

        else:
            response = {
                "status": "failed",
                "message": "This email doesn't belong to any account"
            }
            return Response(
                response,
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetTokenCheckAPIView(APIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):
        # This will be the url of the react app
        FRONTEND_URL = "react_app_url"

        redirect_url = request.GET.get("redirect_url")

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                if len(redirect_url) > 3:
                    return CustomRedirect(redirect_url + "?token_valid=False")
                else:
                    # FRONTEND_URL can also be in an env file
                    return CustomRedirect(f"{FRONTEND_URL}" + "?token_valid=False")

            if redirect_url and len(redirect_url) > 3:
                return CustomRedirect(
                    redirect_url
                    + "?token_valid=True&message=Credentials Valid&uidb64="
                    + uidb64
                    + "&token="
                    + token
                )
            else:
                return CustomRedirect(f"{FRONTEND_URL}" + "?token_valid=False")

        except DjangoUnicodeDecodeError:  # as identifier
            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return CustomRedirect(redirect_url + "?token_valid=False")

            except UnboundLocalError:  # as identifier
                return Response(
                    {"error": "Token is not valid, please request a new one"},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class PasswordResetSetNewPasswordAPIView(GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            response = {
                'status': 'success',
                'message': 'Password Successfully Updated'
            }
            return Response(
                response,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            response = {
                'status': 'failed',
                'message': f"{e}"
            }
            return Response(
                response,
                status=status.HTTP_400_BAD_REQUEST,
            )
        


class UserRetrieveUpdateAPIView(APIView):
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticated,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = UpdateUserSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(request.user, data, partial=True)
        if not serializer.is_valid():
            response = {"status": "failed", "message": serializer.errors}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if profile picture is in request
        if "profile_picture" in data:
            # Delete old profile picture
            if request.user.profile_picture:
                # Get the old profile picture
                old_profile_picture = request.user.profile_picture
                destroy(old_profile_picture.public_id)

            serializer.save(profile_picture=data["profile_picture"])
        else:
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
