from django.db import models

# Create your models here.
class Node(models.Model):
    name = models.CharField(verbose_name="Node name", max_length=30)
    np = models.IntegerField(verbose_name="Number of job slots")
    properties = models.ManyToManyField('NodeProperty')

    def get_nodeproperties(self):
    	return ",".join([ i.name for i in self.properties.all() ])
    get_nodeproperties.short_description = "Node properties"

    def __unicode__(self):
    	return self.name

class NodeProperty(models.Model):
    name = models.CharField(verbose_name="Property name", max_length=50)
    description = models.CharField(verbose_name="Description", max_length=300)

    def __unicode__(self):
    	return self.name
