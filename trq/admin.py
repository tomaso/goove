from goove.trq.models import Node
from goove.trq.models import NodeProperty
from goove.trq.models import NodeState
from goove.trq.models import SubCluster
from goove.trq.models import Job
from goove.trq.models import TorqueServer
from goove.trq.models import User
from goove.trq.models import JobState
from goove.trq.models import Queue
from django.contrib import admin

#class NodePropertyInline(admin.StackedInline):
#	model = NodeProperty
#	extra = 6

class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'subcluster', 'np', 'get_nodeproperties', 'get_nodestates')

class NodePropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class NodeStateAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

class NodeInline(admin.TabularInline):
    model = Node
    extra = 0

class SubClusterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [NodeInline]


class JobAdmin(admin.ModelAdmin):
    list_display = ('jobid', 'job_state', 'job_owner', 'exec_host' )
    

admin.site.register(Node, NodeAdmin)
admin.site.register(NodeProperty, NodePropertyAdmin)
admin.site.register(NodeState, NodeStateAdmin)
admin.site.register(SubCluster, SubClusterAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(TorqueServer)
admin.site.register(User)
admin.site.register(JobState)
admin.site.register(Queue)

# vi:ts=4:sw=4:expandtab
