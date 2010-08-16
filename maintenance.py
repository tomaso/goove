from goove.trq.helpers import getJobState, getQueue, getNode, getTorqueServer, getUser, getGroup, getSubmitHost
from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, TorqueServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count
from goove.trq.helpers import LOG_ERROR,LOG_WARNING,LOG_INFO,LOG_DEBUG,log,feedJobsXML
from django import db

import settings
import subprocess
import time
from xml.parsers.expat import ExpatError
from xml.dom.minidom import parse, parseString

#from guppy import hpy

def removeContent():
    for ns in NodeState.objects.all():
        ns.delete()
    for np in NodeProperty.objects.all():
        np.delete()
    for n in Node.objects.all():
        n.delete()
    for sc in SubCluster.objects.all():
        sc.delete()
    for rj in RunningJob.objects.all():
        rj.delete()
    for j in Job.objects.all():
        j.delete()
#   Job states are inserted initially from initial_data.json
#    for js in JobState.objects.all():
#        js.delete()
    for q in Queue.objects.all():
        q.delete()
    for u in User.objects.all():
        u.delete()


def checkEventsRunningJobs():
    """ Check that Running jobs are running according to the event log
    """
    for rj in Job.objects.filter(job_state__shortname='R'):
        log(LOG_INFO, "Checking job id: %d" % (rj.jobid))
        aes = AccountingEvent.objects.filter(job=rj, type__in=['E','D','A']).count()
        if aes!=0:
            log(LOG_ERROR, "job id: %d, db id: %d is in Running state but accounting records are finished - fixing it." % (rj.jobid, rj.id))
            rj.job_state = getJobState('C')
            rj.save()

def findLostJobs():
    """ Find jobs that are in active state (running) but
    torque server does know about them (mark them as lost).
    """
    for dead_server in TorqueServer.objects.filter(isactive=False):
        for job in Job.objects.filter(job_state=getJobState('R'), server=dead_server):
            job.job_state = getJobState('L')
            job.save()
            log(LOG_DEBUG, "Running job on inactive server marked Lost: %s@%s" % (job.jobid,job.server.name))
    
    for live_server in TorqueServer.objects.filter(isactive=True):
        p = subprocess.Popen(["qstat", "-fx", "@%s" % live_server.name], stdout=subprocess.PIPE)
        (out,err) = p.communicate()
        log(LOG_DEBUG, "Qstat output from live server %s obtained" % (live_server.name))
        try:
            log(LOG_DEBUG, "before parseString()")
            jobsxml = parseString(out)
            log(LOG_DEBUG, "after parseString()")
            starttime = time.time()
            log(LOG_DEBUG, "before feedJobsXML()")
            feedJobsXML(jobsxml, True)
            log(LOG_DEBUG, "after feedJobsXML()")
            endtime = time.time()
            log(LOG_INFO, "feedJobsXML() took %f seconds" % (endtime-starttime))
        except ExpatError:
            log(LOG_ERROR, "Cannot parse line: %s" % (out))
        
        


def findDeletedJobs():
    """ Find deleted jobs (in accounting events table) and mark them as deleted in job table.
    Many jobs have Delete request in AccEvnt table but they are not really deleted (they
    finish ok, or get aborted). This function should filter those.
    """
    # TODO: check that checkEventsRunningJob is still right
    # Evaluation of all the jobs get realy looot of memory 
    # so we get the job one by one

    maxjobid = Job.objects.filter(job_state__shortname='C').aggregate(Max("id"))['id__max']
    for n in range(1,maxjobid+1):
        # clean SQL debug memory once in a while (see http://docs.djangoproject.com/en/1.2/faq/models/#why-is-django-leaking-memory)
        if settings.DEBUG == True and n%1000==0:
            db.reset_queries()
        try:
            j = Job.objects.get(pk=n)
        except Job.DoesNotExist:
            log(LOG_ERROR, "job with pk=%d not found" % (n))
            continue
        aes = AccountingEvent.objects.filter(job=j).order_by("-timestamp")
        ae = aes[0]
        if ae.type=='D':
            j.job_state = getJobState('D')
            j.save()
            log(LOG_DEBUG, "job %s changed to Deleted state" % (j))
        else:
            log(LOG_DEBUG, "job %s unchanged" % (j))
            

def mergeNodes(mergenodesfile):
    """ This function expects file in format of "old_node_name=new_node_name" (without quotes)
    It removes old_node_name node from the database and reassociate all data (e.g. jobs) from this
    old node to the new_node_name node.
    """
    for l in mergenodesfile:
        oldnodename,newnodename = l.strip().split('=')
        try:
            oldnode = Node.objects.get(name=oldnodename)
        except Node.DoesNotExist:
            log(LOG_ERROR, "Old node %s node is not in the database - skipping" % oldnodename)
            continue
            
        try:
            newnode = Node.objects.get(name=newnodename)
        except Node.DoesNotExist:
            log(LOG_ERROR, "New node %s node is not in the database, this is required, sorry - skipping" % newnodename)
            continue

        oldjobslots = JobSlot.objects.filter(node=oldnode)
        for ojs in oldjobslots:
            njs = JobSlot.objects.get(node=newnode,slot=ojs.slot)
            jobs = Job.objects.filter(jobslots=ojs)
            for j in jobs:
                log(LOG_INFO, "For job %s removing jobslot: %s and adding jobslot: %s" % (j,ojs,njs))
                j.jobslots.remove(ojs)
                j.jobslots.add(njs)
                j.save()
            ojs.delete()

        oldnode.delete()

def mergeUsers(mergeusersfile):
    """ This function expects file in format "server:usernameA=usernameB" (without quotes. 
    It reassociates jobs of usernameA to usernameB. After that it deletes usernameA.
    If there are more users with usernameA or usernameB the more precise specification can be used:
    server:usernameA/groupnameA=usernameB/groupnameB
    """
    for l in mergeusersfile:
        oldgroupname = newgroupname = None
        if l.find('/')>=0:
            oldtmp,newtmp = l.strip().split('=')
            oldusername,oldgroupname = oldtmp.split('/')
            newusername,newgroupname = newtmp.split('/')
        else:
            oldusername,newusername = l.strip().split('=')
    
        try:
            if oldgroupname:
                olduser = User.objects.get(name=oldusername, group__name=oldgroupname)
                newuser = User.objects.get(name=newusername, group__name=newgroupname)
            else:
                olduser = User.objects.get(name=oldusername)
                newuser = User.objects.get(name=newusername)
        except User.DoesNotExist:
            log(LOG_ERROR, "Old or new user node is not in the database - skipping line: %s" % l)
            continue

        jobs = Job.objects.filter(job_owner=olduser)
        for j in jobs:
            j.job_owner = newuser
            j.save()
            log(LOG_DEBUG, "Changing the old owner: %s to thenew owner: %s for job %s" % (olduser, newuser, j))


def mergeGroups(mergegroupsfile):
    """ This function expects opened file with lines in format "server:oldgroup=newgroup", where server
    is a name of torque server, oldgroup is the name of the group that should vanish and newgroup is the
    name of the group that should obtain all users belonging to old group. The old group is then deleted.
    """
    for l in mergegroupsfile:
        servername,rest = l.strip().split(':')
        oldgroupname,newgroupname = rest.split('=')
        try:
            oldgroup = Group.objects.get(name=oldgroupname, server__name=servername)
        except Group.DoesNotExist:
            log(LOG_ERROR, "Cannot find group: %s on server %s - skipping" % (oldgroupname, servername))
            continue
        try:
            newgroup = Group.objects.get(name=newgroupname, server__name=servername)
        except Group.DoesNotExist:
            log(LOG_ERROR, "Cannot find group: %s on server %s - skipping" % (newgroupname, servername))
            continue
        for u in User.objects.filter(group=oldgroup):
            u.group = newgroup
            log(LOG_DEBUG, "Changing the old group: %s to the new group: %s for user %s" % (oldgroup, newgroup, u))
        oldgroup.delete()
        log(LOG_DEBUG, "Old group: %s deleted" % (oldgroup))

# vi:ts=4:sw=4:expandtab
