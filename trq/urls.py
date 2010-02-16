from django.conf.urls.defaults import *
from models import Node

nodes = Node.objects.all()

urlpatterns = patterns('',
    (r'^nodes/$', 'django.views.generic.list_detail.object_list', dict(queryset=nodes)),
)
