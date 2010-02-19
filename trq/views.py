from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from models import NodeProperty
from models import NodeState
from django import forms

class BooleanListForm(forms.Form):
    """
    Form with several check ticks.
    """

    def __init__(self,_nameprefix):
        """
        """
        self.nameprefix = _nameprefix
        super(forms.Form, self).__init__()

    def setFields(self, kwds):
        """
        Set the fields in the form
        """
        kwds.sort()
        for k in kwds:
            name = self.nameprefix + k
            self.fields[name] = forms.BooleanField(label=k, required=False)

    def setData(self, dict):
        """
        Set boolean state according to the dictionar
        """
        for key,val in dict.items():
            self.data[key] = val
        self.is_bound = True


def index(request):
    return render_to_response('trq/index.html', {})

def nodes(request):
	return render_to_response('trq/nodes.html', {})

def nodes_overview(request):
#    if request.POST:
#        Node.objects.filter(subcluster__name__in=['saltix','salix'])
#    else:
   
    nodes = Node.objects.all()

    subclusters = [x.name for x in SubCluster.objects.all()]
    properties = [x.name for x in NodeProperty.objects.all()]
    states = [x.name for x in NodeState.objects.all()]
    
    subcluster_form = BooleanListForm('subcluster_')
    subcluster_form.setFields(subclusters)

    properties_form = BooleanListForm('properties_')
    properties_form.setFields(properties)

    states_form = BooleanListForm('states_')
    states_form.setFields(states)

    if request.POST:
        subcluster_form.setData(request.POST)
        properties_form.setData(request.POST)
        states_form.setData(request.POST)
    else:
        subcluster_form.setData( dict(zip(subclusters, len(subclusters)*[True])) )
        properties_form.setData( dict(zip(properties, len(properties)*[True])) )
        states_form.setData( dict(zip(states, len(states)*[True])) )
    return render_to_response(
        'trq/nodes_overview.html', 
        {'nodes_list':nodes, 'subcluster_form':subcluster_form, 
        'properties_form':properties_form, 'states_form':states_form,
        'request_post':request.POST}
        )

# vi:ts=4:sw=4:expandtab
