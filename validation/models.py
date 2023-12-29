from django.db import models
from django.utils import timezone


# Create your models here.
class ValidThingDescription(models.Model):
    name = models.CharField(max_length=100)
    oid = models.CharField(max_length=100)
    agid = models.CharField(max_length=100)
    cid = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    check_date = models.DateField(default=timezone.now)
    is_valid = models.BooleanField(default=False)
    result = models.JSONField(default={"result": "not validated yet"})

    def __str__(self):
        return self.name

class Configuration(models.Model):
    url_server = models.CharField(max_length=200)
    def save(self, *args, **kwargs):
        if Configuration.objects.exists() and not self.pk:
            raise Exception('A configuration already exits.')
        return super(Configuration, self).save(*args, **kwargs)
    def __str__(self):
        return f"{self.url_server}"