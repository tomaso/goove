from django.conf.urls.defaults import *
from piston.resource import Resource
from goove.trqlive.api.handlers import NodeHandler
from emitters import *

node_handler = Resource(NodeHandler)

urlpatterns = patterns('',
    (r'^nodes/(?P<nodename>[^/]+)/', node_handler),
    (r'^nodes/', node_handler, {'emitter_format': 'ext-json'}),
)
