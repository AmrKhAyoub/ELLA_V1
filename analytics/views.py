# analytics/views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Mistake
from .serializers import MistakeSerializer


class MistakeListAPIView(generics.ListAPIView):
    """
    GET: Retrieve all mistakes for the authenticated user.
    Optionally filter by category using a query parameter (e.g., ?category=GRAMMAR).
    """

    serializer_class = MistakeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 1. Get all mistakes for the logged-in user
        queryset = Mistake.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )

        # 2. Check if the frontend wants to filter by a specific category
        category_param = self.request.query_params.get("category")
        if category_param:
            queryset = queryset.filter(category=category_param.upper())

        return queryset
