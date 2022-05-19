from rest_framework.serializers import (
    ModelSerializer,
    EmailField,
    CharField,
    Serializer,
)
from rest_framework.validators import UniqueValidator, ValidationError

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.conf import settings

from uuid import uuid4

from .models import User
from .utils import TokenHandler


class LoginSerializer(Serializer):
    email = EmailField()
    password = CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs["email"], password=attrs["password"])
        if not user:
            raise ValidationError("Incorrect email or password")

        if not user.is_active:
            raise ValidationError("User is not active")
        return {"user": user}


class RegisterSerializer(ModelSerializer):
    email = EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = CharField(write_only=True, required=True, validators=[validate_password])
    password2 = CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "password",
            "password2",
            "email",
            "phone",
            "gender",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data["email"],
            phone=validated_data["phone"],
            gender=validated_data["gender"],
        )
        user.set_password(validated_data["password"])
        user.save()
        token = TokenHandler()
        token.create_token(
            instance=str(settings.CONFIRM_ACCOUNT_PREFIX), user_id=user.id
        )
        send_mail(
            subject="Activate your account!",
            message=f"Your link to activate is: {token.token()}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[
                user.email,
            ],
        )
        return user


class UpdatePasswordSerializer(Serializer):
    password = CharField(write_only=True, required=True, validators=[validate_password])
    password2 = CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise ValidationError("Passwords are not matching")
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data["password"])
        instance.save()
        return instance


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "gender")
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

        def create(self, validated_data):
            pass

        def update(self, instance, validated_data):
            instance.first_name = validated_data.get("first_name", instance.first_name)
            instance.last_name = validated_data.get("last_name", instance.last_name)
            instance.phone = validated_data.get("phone", instance.phone)
            instance.gender = validated_data.get("gender", instance.gender)
            instance.save()
            return instance


class ConfirmAccountSerializer(Serializer):
    def update(self, instance, validated_data=None):
        instance.is_active = True
        instance.save()
        return instance
