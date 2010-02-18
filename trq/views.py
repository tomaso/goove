from django.http import HttpResponse
from django.shortcuts import render_to_response
from models import Node
from models import SubCluster
from django import forms

class BooleanListForm(forms.Form):
    """
    Form with several check ticks.
    """
    def setFields(self, kwds):
        """
        Set the fields in the form
        """
        kwds.sort()
        for k in kwds:
            self.fields[k] = forms.BooleanField(required=False)

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
    nodes = Node.objects.all()
    subclusters = [x.name for x in SubCluster.objects.all()]
    properties = [x.name for x in SubCluster.objects.all()]
    
    subcluster_form = BooleanListForm()
    subcluster_form.setFields(subclusters)
    properties_form = BooleanListForm()
    properties_form.setFields(subpropertiess)
    if request.POST:
        subcluster_form.setData(request.POST)
        properties_form.setData(request.POST)
    else:
        subcluster_form.setData( dict(zip(subclusters, len(subclusters)*[True])) )
        properties_form.setData( dict(zip(propertiess, len(propertiess)*[True])) )
    return render_to_response(
        'trq/nodes_overview.html', 
        {'nodes_list':nodes, 'subcluster_form': subcluster_form, 'properties_form': properties_form,}
        )

# vi:ts=4:sw=4:expandtab
