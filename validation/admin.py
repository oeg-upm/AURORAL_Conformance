from django.contrib import admin
from .models import Configuration, ValidThingDescription, Company, UserProfile

# Register your models here.
admin.site.register(Configuration)
admin.site.register(ValidThingDescription)
admin.site.register(Company)
admin.site.register(UserProfile)