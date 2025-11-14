from django.urls import path
from .views import (CustomUserRegistrationView, 
                    CustomUserLoginView, 
                    CustomUserVerificationView, 
                    CustomUserChangePasswordView, 
                    CustomUserLogoutView, 
                    SendPasswordResetEmailView, 
                    SetNewPasswordView, 
                    GoogleLoginView,
                    UserProfileDetailView,
                    UserProfileUpdateView)

urlpatterns = [
    path('register/', CustomUserRegistrationView.as_view(), name='register'),
    path('login/', CustomUserLoginView.as_view(), name='login'),
    path('verify-email/<uidb64>/<token>/', CustomUserVerificationView.as_view(), name='verify-email'),
    path('logout/', CustomUserLogoutView.as_view(), name='logout'),
    path('change-password/', CustomUserChangePasswordView.as_view(), name='change-password'),
    path('send-reset-password-email/', SendPasswordResetEmailView.as_view(), name='send-reset-password-email'),
    path('reset-password/<uid>/<token>/', SetNewPasswordView.as_view(), name='reset-password'),
    path('google/', GoogleLoginView.as_view(), name='google-login'),
    path('profile/', UserProfileDetailView.as_view(), name='user-profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='update-user-profile'),
]