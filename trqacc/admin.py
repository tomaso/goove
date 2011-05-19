from models import Node
from models import NodeProperty
from models import NodeState
from models import SubCluster
from models import Job
from models import TorqueServer
from models import User
from models import GridUser
from models import Group
from models import JobState
from models import Queue
from models import SubmitHost
from models import GlobalConfiguration
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

class QueueAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    

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
admin.site.register(Queue, QueueAdmin)
admin.site.register(SubmitHost)
admin.site.register(GlobalConfiguration)

# vi:ts=4:sw=4:expandtab
