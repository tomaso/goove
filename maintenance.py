from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, TorqueServer, GridUser, User, Group, JobState, Queue, AccountingEvent
from django.db.models import Avg, Max, Min, Count
from goove.trq.helpers import LOG_ERROR,LOG_WARNING,LOG_INFO,LOG_DEBUG,log

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
    comp_state = JobState.objects.get(shortname='C')
    for rj in Job.objects.filter(job_state__shortname='R'):
        log(LOG_INFO, "Checking job id: %d" % (rj.jobid))
        aes = AccountingEvent.objects.filter(job=rj, type__in=['E','D','A']).count()
        if aes!=0:
            log(LOG_ERROR, "job id: %d, db id: %d is in Running state but accounting records are finished - fixing it." % (rj.jobid, rj.id))
            rj.job_state = comp_state
            rj.save()


def findDeletedJobs():
    """ Find deleted jobs (in accounting events table) and mark them as deleted in job table.
    Many jobs have Delete request in AccEvnt table but they are not really deleted (they
    finish ok, or get aborted). This function should filter those.
    """
    # TODO: check that checkEventsRunningJob is still right
    # Evaluation of all the jobs get realy looot of memory 
    # so we get the job one by one
    maxjobid = Job.objects.filter(job_state__shortname='C').aggregate(Max("id"))['id__max']
    #for n in range(1,maxjobid+1):
    for n in range(916220,maxjobid+1):
        j = Job.objects.get(pk=n)
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
