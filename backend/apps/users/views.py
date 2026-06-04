from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import LoginSerializer, RegisterSerializer, UserProfileSerializer


class RegisterView(APIView):
    """
    POST /api/auth/register/

    Public endpoint — no authentication required.
    Creates a new user account and returns the user's profile data.

    Returns 201 on success, 400 on validation failure.

    Design note: We intentionally do NOT return tokens here. The user must
    explicitly log in. This pattern supports future email verification flows
    without requiring an architectural change.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/auth/login/

    Public endpoint — no authentication required.
    Validates credentials and returns a JWT access + refresh token pair.

    Returns 200 on success, 400 on missing fields, 401 on bad credentials.

    Design note: We generate tokens manually via RefreshToken.for_user()
    rather than using SimpleJWT's TokenObtainPairView so we have full
    control over the response shape (e.g. adding user data later).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    GET /api/auth/me/

    Protected endpoint — requires a valid JWT Bearer token.
    Returns the authenticated user's profile.

    This endpoint serves two purposes:
    1. Lets the frontend fetch the current user's data on app load.
    2. Acts as a canary endpoint for testing authentication in tests.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Re-export SimpleJWT's TokenRefreshView under our URL namespace.
# We wrap it here so we can customise it later (e.g. blacklisting) without
# touching the URL configuration.
TokenRefreshView = TokenRefreshView