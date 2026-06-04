from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom manager for the User model.

    Django's default manager assumes a 'username' field. Since our User
    model uses email as the unique identifier, we override the two required
    methods: create_user and create_superuser.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with a hashed password.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError("An email address is required.")

        email = self.normalize_email(email)  # Lowercases the domain part
        user = self.model(email=email, **extra_fields)
        user.set_password(password)          # Hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser (admin panel access).
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)