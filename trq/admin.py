from goove.trq.models import Node
from goove.trq.models import NodeProperty
from goove.trq.models import NodeState
from goove.trq.models import SubCluster
from goove.trq.models import Job
from goove.trq.models import TorqueServer
from goove.trq.models import User
from goove.trq.models import GridUser
from goove.trq.models import Group
from goove.trq.models import JobState
from goove.trq.models import Queue
from goove.trq.models import SubmitHost
from django.contrib import admin

#class NodePropertyInline(admin.StackedInline):
#	model = NodeProperty
#	extra = 6

class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'subcluster', 'np', 'get_nodeproperties', 'get_nodestates', 'running_jobs_count')

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
    list_display = ('jobid', 'job_state', 'job_owner' )
    

admin.site.register(Node, NodeAdmin)
admin.site.register(NodeProperty, NodePropertyAdmin)
admin.site.register(NodeState, NodeStateAdmin)
admin.site.register(SubCluster, SubClusterAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(TorqueServer)
admin.site.register(User)
admin.site.register(GridUser)
admin.site.register(Group)
admin.site.register(JobState)
admin.site.register(Queue)
admin.site.register(SubmitHost)

# vi:ts=4:sw=4:expandtab
