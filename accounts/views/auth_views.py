from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from ..serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    VerifyPhoneSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from ..services import (
    create_otp,
    verify_otp,
    send_welcome_email,
    send_password_reset_email,
)
from ..models import OTPCode
from core.throttles import (
    LoginRateThrottle,
    RegisterRateThrottle,
    PasswordResetRateThrottle,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginRateThrottle]


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()

    send_welcome_email(user)
    create_otp(user, OTPCode.OTP_TYPE_PHONE)

    refresh = RefreshToken.for_user(user)

    return Response({
        'success': True,
        'message': 'Registration successful. Check your phone for OTP.',
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        },
        'user': {
            'id': str(user.id),
            'email': user.email,
            'full_name': user.full_name,
            'is_owner': user.is_owner,
            'is_renter': user.is_renter,
        },
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass
    return Response({'success': True, 'message': 'Logged out.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_phone(request):
    serializer = VerifyPhoneSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    code = serializer.validated_data['otp_code']
    user = request.user

    if verify_otp(user, code, OTPCode.OTP_TYPE_PHONE):
        user.is_phone_verified = True
        user.save(update_fields=['is_phone_verified'])
        return Response({'success': True, 'message': 'Phone verified successfully.'})

    return Response(
        {'success': False, 'errors': {'otp_code': 'Invalid or expired OTP.'}},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resend_phone_otp(request):
    create_otp(request.user, OTPCode.OTP_TYPE_PHONE)
    return Response({'success': True, 'message': 'OTP sent to your phone.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if not user.check_password(serializer.validated_data['old_password']):
        return Response(
            {'success': False, 'errors': {'old_password': 'Incorrect password.'}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(serializer.validated_data['new_password'])
    user.save()

    return Response({'success': True, 'message': 'Password changed successfully.'})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']

    try:
        user = User.objects.get(email=email)
        otp = create_otp(user, OTPCode.OTP_TYPE_PASSWORD_RESET)
        send_password_reset_email(user, otp.code)
    except User.DoesNotExist:
        pass

    return Response({
        'success': True,
        'message': 'If that email is registered, a reset code has been sent.',
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    code = serializer.validated_data['otp_code']
    new_password = serializer.validated_data['new_password']

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'success': False, 'errors': {'email': 'No account with that email.'}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not verify_otp(user, code, OTPCode.OTP_TYPE_PASSWORD_RESET):
        return Response(
            {'success': False, 'errors': {'otp_code': 'Invalid or expired code.'}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.set_password(new_password)
    user.save()

    return Response({'success': True, 'message': 'Password reset successfully.'})
