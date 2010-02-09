import sys
sys.path.append("..")
import goove
import os

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"

import re

from goove.trq.models import Node
from goove.trq.models import NodeProperty
from goove.trq.models import NodeState
from goove.trq.models import SubCluster

from xml.dom.minidom import parse, parseString


LOG_ERROR=0
LOG_WARNING=1
LOG_INFO=2
LOG_DEBUG=3

def log(level, message):
    print "<%d> %s" % (level, message)

def removeContent():
    for ns in NodeState.objects.all():
        ns.delete()
    for np in NodeProperty.objects.all():
        np.delete()
    for n in Node.objects.all():
        n.delete()
    for sc in SubCluster.objects.all():
        sc.delete()

def feedXML(x):
    sc_regex = re.compile("(\D+)")

    for i in x.childNodes[0].childNodes:
        new_name=i.getElementsByTagName("name")[0].childNodes[0].nodeValue
        new_np=int(i.getElementsByTagName("np")[0].childNodes[0].nodeValue)
        new_properties=i.getElementsByTagName("properties")[0].childNodes[0].nodeValue
        new_states=i.getElementsByTagName("state")[0].childNodes[0].nodeValue
        n = Node(name=new_name, np=new_np)

        # Node's subcluster
        sc_name = sc_regex.search(new_name).groups()[0]
        sc, created = SubCluster.objects.get_or_create(name=sc_name)
        if created:
            log(LOG_INFO, "new subcluster saved: %s" % (sc_name))
        n.subcluster = sc

        n.save()
        log(LOG_INFO, "new node saved: %s" % (new_name))

        # Node properties
        for prop_name in new_properties.split(","):
            prop, created = NodeProperty.objects.get_or_create(name=prop_name, defaults={'description':'No description yet'})
            if not prop:
                log(LOG_ERROR, "property %s could not be created" % (prop_name))
                sys.exit(-1)
            if created:
                prop.save()
                log(LOG_INFO, "new property saved: %s" % (prop_name))
            n.properties.add(prop)

        # Node state(s)
        for state_name in new_states.split(","):
            state, created = NodeState.objects.get_or_create(name=state_name, defaults={'description':'No description yet'})
            if not state:
                log(LOG_ERROR, "state %s could not be created" % (state_name))
                sys.exit(-1)
            if created:
                state.save()
                log(LOG_INFO, "new state saved: %s" % (state_name))
            n.state.add(state)

        n.save()
        

def debugPrint(x):
    for i in x.childNodes[0].childNodes:
        name=i.getElementsByTagName("name")[0].childNodes[0].nodeValue
        np=i.getElementsByTagName("np")[0].childNodes[0].nodeValue
        properties=i.getElementsByTagName("properties")[0].childNodes[0].nodeValue
        print "name: ", name
        print "np: ", np
        print "properties: ", properties
        
    
if __name__=="__main__":
    x = parse("pbsnodes2.xml")

# vi:ts=4:sw=4:expandtab
