from piston.handler import BaseHandler
from trqlive.models import Node

class NodeHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = Node   

    def read(self, request, nodename=None):
        print nodename
        if nodename:
            return Node.objects.get(name=nodename)
        else:
            return Node.objects.all()
    

# vi:ts=4:sw=4:expandtab
        

