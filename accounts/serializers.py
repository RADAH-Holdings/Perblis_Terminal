from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user role fields to the JWT payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['full_name'] = user.full_name
        token['is_owner'] = user.is_owner
        token['is_renter'] = user.is_renter
        token['verification_level'] = user.verification_level
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'phone', 'first_name', 'last_name',
            'password', 'password_confirm',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.is_email_verified = True
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name', 'full_name',
            'profile_photo', 'bio', 'is_renter', 'is_owner',
            'verification_level', 'is_phone_verified', 'is_email_verified',
            'is_id_verified', 'created_at',
        ]
        read_only_fields = [
            'id', 'email', 'verification_level', 'is_phone_verified',
            'is_email_verified', 'is_id_verified', 'created_at',
        ]

    def get_full_name(self, obj):
        return obj.full_name


class PublicUserSerializer(serializers.ModelSerializer):
    """Minimal public-facing user profile. No sensitive fields."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'profile_photo', 'bio',
            'is_owner', 'is_renter', 'verification_level', 'created_at',
        ]

    def get_full_name(self, obj):
        return obj.full_name


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'bio', 'profile_photo']


class UpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['is_owner', 'is_renter']

    def validate(self, attrs):
        is_owner = attrs.get('is_owner', self.instance.is_owner)
        is_renter = attrs.get('is_renter', self.instance.is_renter)
        if not is_owner and not is_renter:
            raise serializers.ValidationError(
                'A user must have at least one role active (owner or renter).'
            )
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(required=True, max_length=6)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )


class VerifyPhoneSerializer(serializers.Serializer):
    otp_code = serializers.CharField(required=True, max_length=6)


class DocumentUploadSerializer(serializers.Serializer):
    document_file = serializers.FileField(required=True)
    document_type = serializers.ChoiceField(
        choices=['government_id', 'business_registration'],
        required=True,
    )
