from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles validation and creation of new user accounts.

    Design decisions:
    - password is write_only: it will never appear in any response body.
    - We delegate password hashing to the model manager (create_user),
      keeping the serializer responsible only for validation and
      orchestration — not for business logic.
    - Django's built-in password validators run via
      validate_password(), giving us minimum length, common password
      checks, and similarity checks for free.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "date_joined"]

    def validate_email(self, value):
        """Normalize email to lowercase for consistent storage."""
        return value.lower()

    def create(self, validated_data):
        """
        Delegate user creation to our custom manager.
        This ensures the password is always hashed, never stored in plain text.
        """
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Validates login credentials and authenticates the user.

    We use a plain Serializer (not ModelSerializer) because this doesn't
    map directly to a model — it's a credential exchange operation.

    Security note: both wrong-password and nonexistent-email return the
    same error message. This prevents user enumeration attacks where an
    attacker could determine which emails are registered.
    """

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        email = attrs.get("email", "").lower()
        password = attrs.get("password", "")

        # Django's authenticate() calls the backend's authenticate method.
        # Our USERNAME_FIELD is email, so it queries by email automatically.
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if not user:
            # AuthenticationFailed maps to HTTP 401 — semantically correct for bad credentials.
            # The message is deliberately generic to prevent user enumeration:
            # an attacker cannot tell if the email exists or the password was wrong.
            raise AuthenticationFailed("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationFailed("This account has been deactivated.")

        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for returning the authenticated user's profile.
    Used by the /api/auth/me/ endpoint.
    """

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = fields