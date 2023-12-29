from django.contrib import admin
from .models import Configuration, ValidThingDescription

# Register your models here.
admin.site.register(Configuration)
admin.site.register(ValidThingDescription)