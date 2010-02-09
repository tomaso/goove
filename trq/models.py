from django.db import models

# Create your models here.
class Node(models.Model):
    ordering = ['name']
    name = models.CharField(verbose_name="Node name", max_length=30)
    np = models.IntegerField(verbose_name="Number of job slots")
    properties = models.ManyToManyField('NodeProperty')
    state = models.ManyToManyField('NodeState')
    subcluster = models.ForeignKey('SubCluster')

    def get_nodeproperties(self):
    	return ",".join([ i.name for i in self.properties.all() ])
    get_nodeproperties.short_description = "Node properties"

    def get_nodestates(self):
    	return ",".join([ i.name for i in self.state.all() ])
    get_nodestates.short_description = "Node state"

    def __unicode__(self):
    	return self.name

class NodeProperty(models.Model):
    name = models.CharField(verbose_name="Property name", max_length=50)
    description = models.CharField(verbose_name="Description", max_length=300)

    def __unicode__(self):
    	return self.name

class NodeState(models.Model):
    name = models.CharField(verbose_name="State name", max_length=30)	
    description = models.CharField(verbose_name="Description", max_length=300)

    def __unicode__(self):
    	return self.name

class SubCluster(models.Model):
    name = models.CharField(verbose_name="Subcluster name", max_length=30)	
    
    def __unicode__(self):
    	return self.name

# vi:ts=4:sw=4:expandtab
