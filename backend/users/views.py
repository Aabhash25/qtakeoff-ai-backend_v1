from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework import permissions
from .serializers import (CustomUserRegistrationSerializer, 
                          CustomUserLoginSerializer, 
                          CustomUserChangePasswordSerializer, 
                          CustomUserLogoutSerailizer, 
                          SendPasswordResetEmailSerializer, 
                          SetNewPasswordSerializer,
                          GoogleAuthSerializer,
                          CustomUserProfileSerializer)
from .models import CustomUser, Role
from django.contrib.auth.models import Group
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken 
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from .utils import generate_verification_email_token
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from .tasks import send_email_verification
from allauth.socialaccount.models import SocialAccount # type: ignore
from django.conf import settings
from google.oauth2 import id_token # type: ignore
from google.auth.transport import requests as google_requests # type: ignore

import logging
logger = logging.getLogger(__name__)


def get_user_token(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class CustomUserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):  # sourcery skip: assign-if-exp, dict-comprehension
        try:
            serializer = CustomUserRegistrationSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                return self._extracted_from_post_5(serializer, request)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as exc:
            error_messages = {}
            for field, messages in exc.detail.items():
                if isinstance(messages, list):
                    error_messages[field] = messages[0] 
                else:
                    error_messages[field] = messages
            return Response(error_messages, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # TODO Rename this here and in `post`
    def _extracted_from_post_5(self, serializer, request):
        user = serializer.save()
        token = get_user_token(user)
        uid, token = generate_verification_email_token(user)
        verification_url = reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
        verification_link = request.build_absolute_uri(verification_url)
        # verification_link = f"{settings.FRONTEND_URL}/api/users/verify-email/{uid}/{token}"
        send_email_verification.delay(
            subject="Verify your email",
            message=f"Click the link to verify your email: {verification_link}",
            to_email=user.email
        )
        return Response({
            "token": token,
            "user": serializer.data,
            "message": "User created successfully! Check your email for verification.",
        }, status=status.HTTP_201_CREATED)
        
class CustomUserVerificationView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            if not user.is_active:
                if default_token_generator.check_token(user, token):
                    user.is_active = True
                    user.save()
                    return Response({"message": "Email verified successfully."}, status=status.HTTP_200_OK)
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CustomUserLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self,request):
        
        try:
            return self._extracted_from_post_(request)
        except ValidationError as exc:
            error_messages = {
                field: messages[0] if isinstance(messages, list) else messages
                for field, messages in exc.detail.items()
            }
            return Response(error_messages, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # TODO Rename this here and in `post`
    def _extracted_from_post_(self, request):
        serializer = CustomUserLoginSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(email=email, password=password)
        if user is None:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        token = get_user_token(user)
        return Response({
            "token": token,
            "user": CustomUserLoginSerializer(user).data,
            "message": "User logged in successfully."
        }, status=status.HTTP_200_OK)

class CustomUserLogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CustomUserLogoutSerailizer

    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response({"message": "User logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as exc:

            error_messages = {
                field: messages[0] if isinstance(messages, list) else messages
                for field, messages in exc.detail.items()
            }
            return Response(error_messages, status=status.HTTP_400_BAD_REQUEST)
    
class CustomUserChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        try:
            serializer = CustomUserChangePasswordSerializer(data=request.data, context={'request': request})
            if not serializer.is_valid(raise_exception=True):
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class SendPasswordResetEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SendPasswordResetEmailSerializer(data=request.data)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save(request=request)
                return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as exc:
            error_messages = {
                field: messages[0] if isinstance(messages, list) else messages
                for field, messages in exc.detail.items()
            }
            return Response(error_messages, status=status.HTTP_400_BAD_REQUEST)
        
class SetNewPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, uid, token, *args, **kwargs):
        try:
            serializer = SetNewPasswordSerializer(data=request.data, context={'uid':uid, 'token':token})
            if serializer.is_valid(raise_exception=True):
                return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as exc:
            error_messages = {
                field: messages[0] if isinstance(messages, list) else messages
                for field, messages in exc.detail.items()
            }
            return Response(error_messages, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        try:
            if serializer.is_valid(raise_exception=True):
                return self._extracted_from_post_5(serializer)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Google login error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # TODO Rename this here and in `post`
    def _extracted_from_post_5(self, serializer):
        token = serializer.validated_data['token']
        role = serializer.validated_data['role']

        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), settings.GOOGLE_CLIENT_ID)

        email = id_info['email']
        first_name = id_info.get('given_name', '')
        last_name = id_info.get('family_name', '')
        username = id_info.get('name', '')
        google_uid = id_info['sub']
        try:
            user = CustomUser.objects.get(email=email)
            created = False
        except CustomUser.DoesNotExist:
            user = CustomUser(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                role=role,
                is_active=True,
            )
            user.set_unusable_password()
            user.save()
            created = True
        SocialAccount.objects.get_or_create(
                user=user,
                provider='google',
                defaults={'uid': google_uid}
            )

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        user_data = {
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": True,

            }

        return Response({
                'refresh': str(refresh),
                'access': access,
                'user': user_data,
                'message': 'Google login successful.'
            }, status=status.HTTP_200_OK)



class UserProfileDetailView(generics.RetrieveAPIView):
    serializer_class = CustomUserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.user_profile


class UserProfileUpdateView(generics.UpdateAPIView):
    serializer_class = CustomUserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return self.request.user.user_profile