import logging
from models import Queue

# batch system stuff
import pbs


def update_queue(queue, conn):
    """ Update live info about the given queue 
    """
    statqueues = pbs.pbs_statque(conn, queue.name.encode('iso-8859-1', 'replace') , [], "")
    if len(statqueues)==0:
        logging.error("pbs_statque failed for queue: %s" % queue.name)
        return
    if len(statqueues)>1:
        logging.warning("pbs_statque returned more than one records for queue: %s" % queue.name)

    attr_dict = dict([ (x.name,x.value) for x in statqueues[0].attribs])
    state_count = attr_dict.pop('state_count')
    state_count_dict=dict([('state_count_'+key.lower(),val) for key,val in [tuple(x.split(':')) for x in state_count.strip().split()]])
    attr_dict.update(state_count_dict)
    for key,val in attr_dict.items():
        setattr(queue,key,val)
    logging.debug("queue: %s updated with live info: %s" % (queue.name, attr_dict))
    queue.save()


def update_queues_all(batchserver_name):
    """ Update info about all queues for give batchserver.
    """
    #batch_connection = pbs.pbs_connect(batchserver_name.encode('iso-8859-1', 'replace'))
    batch_connection = pbs.pbs_connect(batchserver_name.encode('iso-8859-1', 'replace'))
    if batch_connection==-1:
        logging.error("Cannot connect to %s - live data will be missing" % server.name)
        return
    print Queue.objects.filter(server__name=batchserver_name)
    for q in Queue.objects.filter(server__name=batchserver_name):
        update_queue(q, batch_connection)
    pbs.pbs_disconnect(batch_connection)


def update_node(node, conn):
    """ Update live info about the given node 
    """
    global server

    # put node under a subcluster if it does not have any yet
    if not node.subcluster:
        for id,node_regexp in SubCluster.objects.filter(server=n.server).values('id','node_regexp'):
            if re.match(node_regexp,node.name):
                node.subcluster_id = id
                print "node: %s in added to subcluster %s" % (node, node.subcluster)
                break

    statnodes = pbs.pbs_statnode(conn, node.name.encode('iso-8859-1', 'replace') , [], "")
    if len(statnodes)==0:
        logging.error("pbs_statnode failes for node: %s" % node.name)
    if len(statnodes)>1:
        logging.warning("pbs_statnode returned more than one records for node: %s" % node.name)

    attr_dict = dict([ (x.name,x.value) for x in statnodes[0].attribs])
    if attr_dict.has_key('state'):
        node.state.clear()
        for statename in attr_dict['state'].split(','):
            node.state.add(NodeState.objects.get(name=statename.strip()))

    if attr_dict.has_key('properties'):
        node.properties.clear()
        for propertyname in attr_dict['properties'].split(','):
            np,created = NodeProperty.objects.get_or_create(name=propertyname.strip())
            if created:
                logging.warning("New property created: %s" % propertyname)
            node.properties.add(np)

    if attr_dict.has_key('jobs'):
        slot_jobs = dict([tuple(j.strip().split('/')) for j in attr_dict['jobs'].split(',')])
        for slotstr, longjobid in slot_jobs.items():
            slot = int(slotstr)
            js,created = getJobSlot(slot=slot,node=node)
            if created:
                logging.info("new jobslot will be created: slot: %d, node name: %s" % (slot,name))
            jobid = int(longjobid.split('.')[0])
            js.livejob,created = LiveJob.objects.get_or_create(jobid=jobid, server=server)
            if created:
                logging.info("new livejob created: %d" % jobid)
            js.save()

    node.save()

def update_nodes_all(batchserver_name):
    """ Update info about all nodes of the given batchserver.
    """
    batch_connection = pbs.pbs_connect(batchserver_name.encode('iso-8859-1', 'replace'))
    if batch_connection==-1:
        logging.error("Cannot connect to %s - live data will be missing" % server.name)
        return
    print node.objects.filter(server__name=batchserver_name)
    for n in node.objects.filter(server__name=batchserver_name):
        update_node(n, batch_connection)
    pbs.pbs_disconnect(batch_connection)
    

# vi:ts=4:sw=4:expandtab
