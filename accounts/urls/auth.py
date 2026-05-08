from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views.auth_views import (
    LoginView,
    register,
    logout,
    verify_phone,
    resend_phone_otp,
    change_password,
    password_reset_request,
    password_reset_confirm,
)

urlpatterns = [
    path('register/', register, name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('logout/', logout, name='auth-logout'),
    path('verify-phone/', verify_phone, name='auth-verify-phone'),
    path('resend-otp/', resend_phone_otp, name='auth-resend-otp'),
    path('password/change/', change_password, name='auth-password-change'),
    path('password/reset/', password_reset_request, name='auth-password-reset'),
    path('password/reset/confirm/', password_reset_confirm, name='auth-password-reset-confirm'),
]
