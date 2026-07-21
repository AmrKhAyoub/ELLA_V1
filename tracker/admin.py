from django.contrib import admin  # noqa: F401

from .models import EnrichedPlace, UserCurrentLocation  # noqa: F401

# Register your models here.
admin.site.register(UserCurrentLocation)
admin.site.register(EnrichedPlace)
