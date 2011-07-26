import logging,re,datetime
from models import Queue,Node,SubCluster,NodeState,NodeProperty,LiveJob,BatchServer,JobState
from helpers import getJobSlot,getQueue,getBatchServer,GlobalConfiguration,getNode
from django.db.models import Q
from django.db import transaction, connection

# batch system stuff
import pbs

pbs_data_nodes = {}
pbs_data_jobs = {}

def update_one_queue_from_pbs_data(queue, attr_dict):
    state_count = attr_dict.pop('state_count')
    state_count_dict=dict([('state_count_'+key.lower(),val) for key,val in [tuple(x.split(':')) for x in state_count.strip().split()]])
    attr_dict.update(state_count_dict)
    for key,val in attr_dict.items():
        setattr(queue,key,val)
    logging.debug("queue: %s updated with live info: %s" % (queue.name, attr_dict))


def update_one_queue(queue):
    """ Update live info about the given queue 
    """
    conn = pbs.pbs_connect(queue.server.name.encode('iso-8859-1', 'replace'))
    if conn==-1:
        logging.error("Cannot connect to %s - live data will be missing" % server.name)
        return
    statqueues = pbs.pbs_statque(conn, queue.name.encode('iso-8859-1', 'replace') , [], "")
    pbs.pbs_disconnect(conn)
    if len(statqueues)==0:
        logging.error("pbs_statque failed for queue: %s" % queue.name)
        return
    if len(statqueues)>1:
        logging.warning("pbs_statque returned more than one records for queue: %s" % queue.name)

    attr_dict = dict([ (x.name,x.value) for x in statqueues[0].attribs])
    update_one_queue_from_pbs_data(queue, attr_dict)
    queue.save()


def update_all_queues(batchserver_name):
    """ Update info about all queues for give batchserver.
    """
    server,created = getBatchServer(batchserver_name)
    if server.queues_lastupdate and (datetime.datetime.now()-server.queues_lastupdate).total_seconds()<GlobalConfiguration.objects.get(pk=1).max_lastupdate:
        logging.debug("Queue info is new enough for server: %s" % batchserver_name)
        return

    conn = pbs.pbs_connect(batchserver_name.encode('iso-8859-1', 'replace'))
    if conn==-1:
        logging.error("Cannot connect to %s - live data will be missing" % server.name)
        return
    statqueues = pbs.pbs_statque(conn, "" , [], "")
    pbs.pbs_disconnect(conn)
    if conn==-1:
        logging.error("Cannot connect to %s - live data will be missing" % server.name)
        return
    
    for sq in statqueues:
        queue,created = getQueue(sq.name, server)
        attr_dict = dict([ (x.name,x.value) for x in sq.attribs])
        update_one_queue_from_pbs_data(queue, attr_dict)
        queue.save()
    server.queues_lastupdate = datetime.datetime.now()
    server.save()


def update_one_node_from_pbs_data(node, attr_dict):
    """ Update node info from pbs data
    """
    # put node under a subcluster if it does not have any yet
    if not node.subcluster:
        for id,node_regexp in SubCluster.objects.filter(server=node.server).values_list('id','node_regexp'):
            if re.match(node_regexp,node.name):
                node.subcluster_id = id
                node.save()
                break
    # fill node's np if it is not present
    if not node.np:
        node.np = attr_dict['np']
        node.save()

    new_states = []
    if attr_dict.has_key('state'):
#        node.state.clear()
        for statename in attr_dict['state'].split(','):
            #node.state.add(NodeState.objects.get(name=statename.strip()))
            new_states.append(NodeState.objects.get(name=statename.strip()))
    attr_dict['state'] = new_states


    new_properties = []
    if attr_dict.has_key('properties'):
#        node.properties.clear()
        for propertyname in attr_dict['properties'].split(','):
            np,created = NodeProperty.objects.get_or_create(name=propertyname.strip())
            if created:
                print("New property created: %s" % propertyname)
            new_properties.append(np)
#            node.properties.add(np)
    attr_dict['properties'] = new_properties

    new_jobs = []
    if attr_dict.has_key('jobs'):
        slot_jobs = dict([tuple(j.strip().split('/')) for j in attr_dict['jobs'].split(',')])
        for slotstr, longjobid in slot_jobs.items():
            slot = int(slotstr)
#            js,created = getJobSlot(slot=slot,node=node)
#            if created:
#                logging.info("new jobslot will be created: slot: %d, node name: %s" % (slot,name))
            jobid = int(longjobid.split('.')[0])
            new_jobs.append(jobid)
            
#            js.livejob,created = LiveJob.objects.get_or_create(jobid=jobid, server=node.server)
#            if created:
#                logging.info("new livejob created: %d" % jobid)
#            js.save()
    attr_dict['jobs'] = new_jobs
    return attr_dict


def update_one_node(node):
    """ Update live info about the given node 
    """
    conn = pbs.pbs_connect(node.server.name.encode('iso-8859-1', 'replace'))
    if conn==-1:
        logging.error("Cannot connect to %s - live data will be missing" % server.name)
        return
    statnodes = pbs.pbs_statnode(conn, node.name.encode('iso-8859-1', 'replace') , [], "")
    pbs.pbs_disconnect(conn)

    if len(statnodes)==0:
        logging.error("pbs_statnode failed for node: %s" % node.name)
        return
    if len(statnodes)>1:
        logging.warning("pbs_statnode returned more than one records for node: %s" % node.name)

    attr_dict = dict([ (x.name,x.value) for x in statnodes[0].attribs])
    update_one_node_from_pbs_data(node, attr_dict)
    node.save()


def update_all_nodes(batchserver_name):
    """ Update info about all nodes of the given batchserver.
    """
    server,created = getBatchServer(batchserver_name)
    if not pbs_data_nodes.has_key(batchserver_name):
        pbs_data_nodes[batchserver_name] = {'last_update':None, 'nodes':{}}

    if pbs_data_nodes[batchserver_name]['last_update'] and (datetime.datetime.now()-pbs_data_nodes[batchserver_name]['last_update']).total_seconds()<GlobalConfiguration.objects.get(pk=1).max_lastupdate:
        logging.debug("Nodes info is new enough for server: %s" % batchserver_name)
        print "not updated"
        return pbs_data_nodes

    print "updated"

    conn = pbs.pbs_connect(batchserver_name.encode('iso-8859-1', 'replace'))
    if conn==-1:
        logging.error("Cannot connect to %s - live data will be missing" % server.name)
        return
    statnodes = pbs.pbs_statnode(conn, "" , [], "")
    pbs.pbs_disconnect(conn)

    for sn in statnodes:
        node,created = getNode(sn.name, server)
        attr_dict = dict([ (x.name,x.value) for x in sn.attribs])
        pbs_data_nodes[batchserver_name]['nodes'][node] = update_one_node_from_pbs_data(node, attr_dict)
        pbs_data_nodes[batchserver_name]['last_update'] = datetime.datetime.now()

    return pbs_data_nodes


def update_one_job_from_pbs_data(jobid, attr_dict):
    if attr_dict.has_key('job_state'):
        attr_dict['job_state'] = JobState.objects.get(shortname=attr_dict['job_state'])
    if attr_dict.has_key('queue'):
        attr_dict['queue'] = Queue.objects.get(name=attr_dict['queue'], server__name=attr_dict['server'])
    return attr_dict


def update_all_jobs(batchserver_name):
    """ Update info about all jobs of the given batchserver.
    """
    server,created = getBatchServer(batchserver_name)
    if not pbs_data_jobs.has_key(batchserver_name):
        pbs_data_jobs[batchserver_name] = {'last_update':None, 'jobs':{}}

    if pbs_data_jobs[batchserver_name]['last_update'] and (datetime.datetime.now()-pbs_data_jobs[batchserver_name]['last_update']).total_seconds()<GlobalConfiguration.objects.get(pk=1).max_lastupdate:
        logging.debug("jobs info is new enough for server: %s" % batchserver_name)
        print "not updated"
        return pbs_data_jobs
    print "updated"

    conn = pbs.pbs_connect(batchserver_name.encode('iso-8859-1', 'replace'))
    if conn==-1:
        logging.error("Cannot connect to %s - live data will be missing" % server.name)
        return
    statjobs = pbs.pbs_statjob(conn, "" , [], "")
    pbs.pbs_disconnect(conn)

    for sj in statjobs:
        jobid = sj.name
        attr_dict = dict([ (x.name,x.value) for x in sj.attribs])
        attr_dict = {}
        for x in sj.attribs:
            if x.resource:
                attr_dict[x.name+"_"+x.resource] = x.value
            else:
                attr_dict[x.name] = x.value

        pbs_data_jobs[batchserver_name]['jobs'][jobid] = update_one_job_from_pbs_data(jobid, attr_dict)
        pbs_data_jobs[batchserver_name]['last_update'] = datetime.datetime.now()

    return pbs_data_jobs




    

# vi:ts=4:sw=4:expandtab
