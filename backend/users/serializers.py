from rest_framework import serializers, exceptions
from .models import CustomUser, Role, CustomUserProfile
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .utils import password_validation
from rest_framework_simplejwt.tokens import RefreshToken,TokenError # type: ignore
from django.urls import reverse
from .tasks import send_rest_password_email



class CustomUserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'role', 'password', 'password2']
        extra_kwargs = {
            'email': {'required': True, 'validators': []},
            'username': {'required': True, 'validators': []},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['role'].choices = [
                (Role.USER, 'User'),
                (Role.ESTIMATOR, 'Estimator')
            ]

    def validate_email(self, value):
        role = self.initial_data.get('role', Role.USER).lower()
        domain = value.split('@')[-1].lower()

        if role == Role.USER:
            allowed_domains = ['gmail.com', 'outlook.com']
            if domain not in allowed_domains:
                raise serializers.ValidationError(_("Only Gmail and Outlook email addresses are allowed for normal users."))

        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("This Email is already in use."))

        return value
     
        
    def validate_username(self, value):
        if CustomUser.objects.filter(username=value):
            raise serializers.ValidationError(_("Username is already in use."))
        return value
        

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": _("Passwords do not match.")})
        try:
            password_validation(attrs['password'])
            validate_password(attrs['password'])
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)}) from e
        return attrs 
    
    def create(self, validated_data):
        validated_data.pop('password2')
        role = validated_data.pop('role', Role.USER)
        email = validated_data['email']
        if role not in [Role.ADMIN, Role.USER, Role.ESTIMATOR]:
            raise serializers.ValidationError(_("Invalid role."))
        if role == Role.ESTIMATOR and not email.endswith('@ssnbuilders.com'):
            raise ValueError('Estimators must use an @ssnbuilders.com email address.')
        user = CustomUser(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=role,
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
class CustomUserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'first_name', 'last_name', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'password': {'required': True},
            'first_name': {'read_only': True},
            'last_name': {'read_only': True},
            'role': {'read_only': True},
        }

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(email=attrs['email'])
            if not user.is_active:
                raise serializers.ValidationError(_("Email is not verified. Go and check your email!"))
            if not user.check_password(attrs['password']):
                raise serializers.ValidationError(_("Incorrect password."))
        except CustomUser.DoesNotExist as e:
            raise serializers.ValidationError(_("Invalid login credentials.")) from e
        return attrs

    def to_representation(self, instance):
        return {
            'email': instance.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'role': instance.role,
        }


class CustomUserLogoutSerailizer(serializers.Serializer):
    refresh = serializers.CharField(required=True) 

    default_error_messages = {
        'bad_token': _('Token is invalid or expired')
    }
        
    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')

class CustomUserChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['old_password', 'new_password', 'new_password2']
        extra_kwargs = {
            'old_password': {'required': True},
            'new_password': {'required': True},
            'new_password2': {'required': True},
        }
    
    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError(_("Old password is incorrect."))
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"password": _("New passwords do not match.")})
        try:
            password_validation(attrs['new_password'])
            validate_password(attrs['new_password'])
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)}) from e
        return attrs
    
class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    class Meta:
        fields = ['email']
    
    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(_("This email is not registered."))
        if not value.endswith('@gmail.com') and not value.endswith('@outlook.com') and not value.endswith('@ssnbuilders.com'):
            raise serializers.ValidationError(_("Only Gmail and Outlook email addresses are allowed."))
        user = CustomUser.objects.get(email=value)
        if not user.is_active:
            raise serializers.ValidationError(_("Email is not verified. Please check your inbox."))
        return value

    def save(self, request):
        email = self.validated_data['email']
        print(email)
        user = CustomUser.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        reset_password_url = reverse('reset-password', kwargs={'uid': uid, 'token': token})
        reset_password_link = request.build_absolute_uri(reset_password_url)
        # reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        message = f"Click the link below to reset your password:\n\n{reset_password_link}"

        send_rest_password_email.delay(
            subject="Reset your password",
            message=message,
            to_email=[user.email],
        )

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    password2 = serializers.CharField(required=True, write_only=True)

    class Meta:
        fields = ['password', 'password2']
    
    def validate(self, attrs):
        try:
            uid = self.context['uid']
            token = self.context['token']
            if attrs['password'] != attrs['password2']:
                raise serializers.ValidationError({"password": _("Passwords do not match.")})
            password_validation(attrs['password'])
            validate_password(attrs['password'])
            user_id = smart_str(urlsafe_base64_decode(uid))
            if not CustomUser.objects.filter(pk=user_id).exists():
                raise serializers.ValidationError(_("User does not exist."))
            user = CustomUser.objects.get(pk=user_id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise serializers.ValidationError(_("Token is invalid or expired."))
            user.set_password(attrs['password'])
            user.save()
            return attrs
        except DjangoUnicodeDecodeError as e:
            raise serializers.ValidationError(
                _(
                    "Token is invalid or expired. Exception: DjangoUnicodeDecodeError"
                )
            ) from e
        except exceptions.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)}) from e
        
class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=Role.choices, default=Role.USER)
    
    def validate(self, attrs):
        token = attrs.get('token')
        role = attrs.get('role')
        if not token:
            raise serializers.ValidationError("Token is required.")
        if not role:
            raise serializers.ValidationError("Role is required.")
        return attrs
    

class CustomUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUserProfile
        fields = ['id', 'user', 'mobile_number']
        read_only_fields = ['user']