# tracker/views.py
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import process_location_task


class UpdateLocationAPIView(APIView):
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR", "8.8.8.8")

    def post(self, request, *args, **kwargs):
        # Fallback: Get or Create a dummy user since no Auth is implemented yet
        user, _ = User.objects.get_or_create(username="default_user")

        lat = request.data.get("latitude")
        lon = request.data.get("longitude")
        ip = self.get_client_ip(request)

        # Pass the task to Celery asynchronously
        process_location_task.delay(user.id, lat, lon, ip)

        return Response(
            {"message": "Location received. Processing in background..."},
            status=status.HTTP_202_ACCEPTED,
        )
