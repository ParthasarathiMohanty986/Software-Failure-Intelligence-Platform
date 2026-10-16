from django.contrib.auth import authenticate, get_user_model, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer

User = get_user_model()


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response({"id": user.id, "username": user.username, "email": user.email}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(username=serializer.validated_data["username"], password=serializer.validated_data["password"])
        if user is None:
            raise serializers.ValidationError({"detail": "Invalid username or password"})
        login(request, user)
        return Response({"id": user.id, "username": user.username, "email": user.email}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out"}, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MeView(APIView):
    def get(self, request):
        user = request.user
        return Response({"id": user.id, "username": user.username, "email": user.email})
