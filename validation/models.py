from django.db import models
from django.utils import timezone


class ValidThingDescription(models.Model):
    name = models.CharField(max_length=100)
    property = models.CharField(max_length=100)
    oid = models.CharField(max_length=100)
    agid = models.CharField(max_length=100)
    cid = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    check_date = models.DateField(default=timezone.now)
    is_valid = models.BooleanField(default=False)
    conformance_status = models.IntegerField(default=0)
    reportInfo = models.CharField(max_length=100, default="Not Checked")

    def __str__(self):
        return self.name


class Configuration(models.Model):
    url_server = models.CharField(max_length=200)
    oid = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if Configuration.objects.exists() and not self.pk:
            raise Exception('A configuration already exits.')
        return super(Configuration, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.url_server}, {self.oid}"

