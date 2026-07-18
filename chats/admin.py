from django.contrib import admin

from chats.models import Message, Session

# Register your models here.
admin.site.register(Session)
admin.site.register(Message)
