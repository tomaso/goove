from django.db import models
import datetime

# Create your models here.

class Node(models.Model):
    name = models.CharField(verbose_name="node name", max_length=30)

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
    	return self.name


class TorqueServer(models.Model):
    name = models.CharField(verbose_name="torque server full hostname", max_length=100)
    def __unicode__(self):
    	return self.name

 
# vi:ts=4:sw=4:expandtab
