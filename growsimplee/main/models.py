from django.db import models

# Create your models here.

class Product(models.Model):
    productID = models.CharField(max_length=200)
    volume = models.FloatField(null=True,blank=True)
    delivered = models.BooleanField(default=False)
    assigned = models.BooleanField(default=False)
    sourceAddress = models.CharField(max_length=200,null=True,blank=True)
    sourceLatitude = models.FloatField(null=True,blank=True)
    sourceLongitude = models.FloatField(null=True,blank=True)
    destinationAddress = models.CharField(max_length=200,null=True,blank=True)
    destinationLatitude = models.FloatField(null=True,blank=True)
    destinationLongitude = models.FloatField(null=True,blank=True)
    person = models.CharField(max_length=200,null=True,blank=True)

class Driver(models.Model):
    person = models.CharField(max_length=200,null=True,blank=True)
    path = models.CharField(max_length=200,null=True,blank=True)
    active = models.BooleanField(default=True)
    assigned = models.BooleanField(default=False)
