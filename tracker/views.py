# tracker/views.py
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import process_location_task


class HelloWorldView(APIView):
    def get(self, request):
        return Response({"message": "Hello World wefjhwarlhg"})


@method_decorator(csrf_exempt, name="dispatch")
class UpdateLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "8.8.8.8")

        # If the IP is localhost, replace it with a public IP for testing purposes
        if ip in ["127.0.0.1", "::1"]:
            ip = "8.8.8.8"  # IP of Google Public DNS for testing

        return ip

    def post(self, request, *args, **kwargs):
        # user, _ = User.objects.get_or_create(id=1, defaults={"username": "test_user_1"})
        user = request.user
        # extract latitude and longitude from the request data
        lat = request.data.get("latitude")
        lon = request.data.get("longitude")
        ip = self.get_client_ip(request)

        # treat empty strings as None for latitude and longitude
        if lat == "" or lon == "":
            lat, lon = None, None

        # Pass the task to Celery asynchronously
        process_location_task.delay(user.id, lat, lon, ip)

        return Response(
            {"message": "Location received. Processing in background..."},
            status=status.HTTP_202_ACCEPTED,
        )
