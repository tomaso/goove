from goove.trq.models import Node
from goove.trq.models import NodeProperty
from goove.trq.models import NodeState
from goove.trq.models import SubCluster
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

admin.site.register(Node, NodeAdmin)
admin.site.register(NodeProperty, NodePropertyAdmin)
admin.site.register(NodeState, NodeStateAdmin)
admin.site.register(SubCluster, SubClusterAdmin)
