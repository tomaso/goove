from goove.trq.models import Node
from goove.trq.models import NodeProperty
from django.contrib import admin

#class NodePropertyInline(admin.StackedInline):
#	model = NodeProperty
#	extra = 6

class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'np', 'get_nodeproperties')

class NodePropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

admin.site.register(Node, NodeAdmin)
admin.site.register(NodeProperty, NodePropertyAdmin)
