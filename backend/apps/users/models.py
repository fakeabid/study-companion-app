import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the AI Study Companion.

    Design decisions:
    - UUID primary key: prevents ID enumeration attacks and is safe to
      expose in URLs without leaking database row counts.
    - Email as USERNAME_FIELD: removes the username concept entirely.
      Students identify themselves by email, which is universally understood.
    - AbstractBaseUser: gives us full control. AbstractUser would carry a
      'username' field we'd never use and would have to work around.
    - PermissionsMixin: adds is_superuser, groups, and user_permissions,
      which are needed for the Django admin and future role-based access.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(
        unique=True,
        max_length=254,  # RFC 5321 maximum length for an email address
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"        # Used by authenticate() and login forms
    REQUIRED_FIELDS = []            # Only asked for when running createsuperuser

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()