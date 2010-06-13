from django.db import models

# Create your models here.

class UnixUser(models.Model):
    name = models.CharField(verbose_name="Unix user name", max_length=100)

    def __unicode__(self):
        return self.name

class GridUser(models.Model):
    dn = models.CharField(verbose_name="DN of the grid user", max_length=256)

    def __unicode__(self):
        return self.dn

class Grid2UnixMapping(models.Model):
    start_time = models.DateTimeField(verbose_name='Start time')
    end_time = models.DateTimeField(verbose_name='End time')
    griduser = models.ForeignKey(GridUser)
    unixuser = models.ForeignKey(UnixUser)

class ClientNode(models.Model):
    name = models.CharField(verbose_name="node name", max_length=30)

    def __unicode__(self):
        return self.name

class ServerNode(models.Model):
    name = models.CharField(verbose_name="node name", max_length=30)

    def __unicode__(self):
        return self.name

TRANSFER_CHOICES = (
    ('RETR', 'Retrieve'),
    ('STOR', 'Store'),
)

# TODO: remove the null tollerance
class Transfer(models.Model):
    clientnode = models.ForeignKey(ClientNode, null=True)
    servernode = models.ForeignKey(ServerNode, null=True)
    griduser = models.ForeignKey(GridUser, null=True)
    unixuser = models.ForeignKey(UnixUser, null=True)
    start_time = models.DateTimeField(verbose_name='Start time', null=True)
    comp_time = models.DateTimeField(verbose_name='Completion time', null=True)
    type = models.CharField(max_length=4, choices=TRANSFER_CHOICES, null=True)
    file = models.CharField(verbose_name="File name", max_length=512)

    

# vi:ts=4:sw=4:expandtab
