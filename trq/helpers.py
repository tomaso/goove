from django import forms
from models import Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, TorqueServer, User, Group, JobState, Queue, AccountingEvent, SubmitHost
import subprocess
from xml.dom.minidom import parse, parseString
from xml.parsers.expat import ExpatError
import signal
import re
import time
import datetime

LOG_ERROR=0
LOG_WARNING=1
LOG_INFO=2
LOG_DEBUG=3

JobStateCache = {}
QueueCache = {}
NodeCache = {}
TorqueServerCache = {}
UserCache = {}
GroupCache = {}
SubmitHostCache = {}

Configuration = {
    'loglevel': LOG_DEBUG
}

def log(level, message):
    if level <= Configuration['loglevel']:
        print "<%d> %s" % (level, message)

#
# Caching functions, we do not have one for Jobs as there are too many of them
#
def getJobState(state):
    """
    Get JobState db object (from cache or database). Valid states are: Q,R,C,L
    """
    global JobStateCache
    if not JobStateCache.has_key(state):
        JobStateCache[state] =  JobState.objects.get(shortname=state)
    return JobStateCache[state]


def getQueue(qname):
    """
    Return tuple (queue object, created)
    """
    global QueueCache
    created = False
    if not QueueCache.has_key(qname):
        QueueCache[qname],created = Queue.objects.get_or_create(name=qname)
    return (QueueCache[qname],created)

def getNode(nname):
    global NodeCache
    created = False
    if not NodeCache.has_key(nname):
        NodeCache[nname],created = Node.objects.get_or_create(name=nname)
    return (NodeCache[nname],created)

def getTorqueServer(tsname):
    global TorqueServerCache
    created = False
    if not TorqueServerCache.has_key(tsname):
        TorqueServerCache[tsname],created = TorqueServer.objects.get_or_create(name=tsname)
    return (TorqueServerCache[tsname],created)

def getUser(uname, group=None):
    global UserCache
    created = False
    if not UserCache.has_key(uname):
        UserCache[uname],created = User.objects.get_or_create(name=uname, group=group)
    return (UserCache[uname],created)

def getGroup(gname):
    global GroupCache
    created = False
    if not GroupCache.has_key(gname):
        GroupCache[gname],created = Group.objects.get_or_create(name=gname)
    return (GroupCache[gname],created)

def getSubmitHost(shname):
    global SubmitHostCache
    created = False
    if not SubmitHostCache.has_key(shname):
        SubmitHostCache[shname],created = SubmitHost.objects.get_or_create(name=shname)
    return (SubmitHostCache[shname],created)


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

    def setData(self, dict, useprefix=True):
        """
        Set boolean state according to the dictionary
        """
        for key,val in dict.items():
            if useprefix:
                self.data[self.nameprefix+key] = val
            else:
                self.data[key] = val
        self.is_bound = True


def getTimeOrZero(xmlnode, attrname):
    """
    Get attribute value from xml as integer.
    If not present, return 0.
    """
    l = xmlnode.getElementsByTagName(attrname)
    if len(l)==0:
        return None
    t = l[0].childNodes[0].nodeValue
    dt = datetime.datetime.fromtimestamp(int(t))
    # YYYY-MM-DD HH:MM[:ss[.uuuuuu]]
    return "%s-%s-%s %s:%s:%s" % (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

            
def feedJobsXML(x, cleanLostJobs=False):
    """
    Parse xml produced with qstat -fx and feed the data into django
    data structures.
    """
    JOBID_REGEX = re.compile("(\d+)\.(.*)")

    updated_jobs = []

    for i in x.childNodes[0].childNodes:
        #new_full_jobid = i.getElementsByTagName("Job_Id")[0].childNodes[0].nodeValue
        # currently the job id is text element and it is the first child of the <Job> element
        new_full_jobid = i.firstChild.nodeValue
        new_jobid_name, new_server_name = JOBID_REGEX.search(new_full_jobid).groups()

        new_server,created = TorqueServer.objects.get_or_create(name=new_server_name)
        if created:
            log(LOG_INFO, "new server will be created: %s" % new_server_name)

        new_job,created = Job.objects.get_or_create(jobid=int(new_jobid_name), server=new_server)
        if created:
            log(LOG_INFO, "new job will be created: %s" % new_jobid_name)
        else:
            log(LOG_INFO, "job already exists (will only update data): %s" % new_jobid_name)

        # job_owner
        new_job_owner_name = i.getElementsByTagName("Job_Owner")[0].childNodes[0].nodeValue
        new_job_owner_name = new_job_owner_name.split("@")[0]
        new_job_owner,created = User.objects.get_or_create(name=new_job_owner_name)
        if created:
            log(LOG_INFO, "new user will be created: %s" % new_job_owner_name)
        new_job.job_owner = new_job_owner

        # used resources
        restag_list = i.getElementsByTagName("resources_used")
        if len(restag_list)>0:
            restag = restag_list[0]
            # cput
            new_cput_string = restag.getElementsByTagName("cput")[0].childNodes[0].nodeValue
            h,m,s = new_cput_string.split(":")
            new_job.cput = (int(h)*60+int(m))*60+int(s)
            # walltime
            new_walltime_string = restag.getElementsByTagName("walltime")[0].childNodes[0].nodeValue
            h,m,s = new_walltime_string.split(":")
            new_job.walltime = (int(h)*60+int(m))*60+int(s)
            if new_job.walltime!=0:
                new_job.efficiency = 100*new_job.cput/new_job.walltime
            else:
                new_job.efficiency = 0

        # job state
        new_job_state_abbrev = i.getElementsByTagName("job_state")[0].childNodes[0].nodeValue
        new_job_state = JobState.objects.get(shortname=new_job_state_abbrev)
        new_job.job_state = new_job_state

        # queue
        new_queue_name = i.getElementsByTagName("queue")[0].childNodes[0].nodeValue
        new_queue,created = Queue.objects.get_or_create(name=new_queue_name)
        if created:
            log(LOG_INFO, "new queue will be created: %s" % new_queue_name)
        new_job.queue = new_queue

        # ctime
        new_job.ctime = getTimeOrZero(i, "ctime")
        # mtime
        new_job.mtime = getTimeOrZero(i, "mtime")
        # qtime
        new_job.qtime = getTimeOrZero(i, "qtime")
        # etime
        new_job.etime = getTimeOrZero(i, "etime")
        # start_time
        new_job.start_time = getTimeOrZero(i, "start_time")
        # comp_time
        new_job.comp_time = getTimeOrZero(i, "comp_time")

        # TODO: redesign for multislot jobs
        # exec_host
        exec_host_xml = i.getElementsByTagName("exec_host")
        if len(exec_host_xml)>0:
            new_exec_host_name = exec_host_xml[0].childNodes[0].nodeValue
            new_exec_host_name = new_exec_host_name.split("/",1)[0]
            new_exec_host,created = Node.objects.get_or_create(name=new_exec_host_name)
            if created:
                log(LOG_INFO, "new node (exec_host) will be created: %s" % new_exec_host_name)
            new_job.exec_host = new_exec_host
        
        new_job.save()
        updated_jobs.append(new_job)
    # check that not finished jobs are between recently updated jobs
    # otherwise it is kinda lost job
    if cleanLostJobs:
        ljs = getJobState('L')
        for j in Job.objects.exclude(job_state__shortname="C").exclude(job_state__shortname="L"):
            if j not in updated_jobs:
                log(LOG_WARNING, "job %d.%s is in database unfinished but not present in torque anymore - job is Lost" % (j.jobid, j.server.name))
                j.job_state = getJobState('L')
                j.save()
            


class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise Alarm

def UpdateRunningJob(job):
    """
    Update data of a running job from torque server
    Currently only xml output of `qstat -x` is supported
    Returns True if the update was succesful. 
    Returns False if the job could not be updated and it is then moved
    to lost jobs.
    """
    # if the data feeder is currently running, some jobs may be marked Lost by mistake, but when the
    # feeder runs again it finishes them correctly (switch them from Lost to Completed)

#    TODO: does not work in multithreaded environment
#    signal.signal(signal.SIGALRM, alarm_handler)
#    signal.alarm(20)
    try:
        starttime = time.time()
        proc = subprocess.Popen(["qstat", "-x", "%s.%s" % (job.jobid, job.server.name)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = proc.communicate()
        if stderrdata and stderrdata.startswith("qstat: Unknown Job Id"):
            log(LOG_INFO, "UpdateRunningJob() job %s.%s is in database unfinished but not present in torque anymore - job is Lost" % (job.jobid, job.server.name))
            job.job_state = getJobState('L')
            job.save()
            return False
            
        log(LOG_INFO, "UpdateRunningJob() parsing: %s" % stdoutdata)
#        signal.alarm(0)  # reset the alarm
        jobsxml = parseString(stdoutdata)
        feedJobsXML(jobsxml)
        jobsxml.unlink()
        endtime = time.time()
        log(LOG_INFO, "UpdateRunningJob() took %f seconds" % (endtime-starttime))
    except Alarm:
        log(LOG_ERROR, "UpdateRunningJob() taking too long.")
    except ExpatError:
        log(LOG_ERROR, "Cannot parse line: %s, jobid: %s.%s" % (stdoutdata, job.jobid, job.server.name))
    return True

def getRunningCountQstat():
    """
    Get number of running jobs from output of qstat
    """
    out,err = subprocess.Popen(["/bin/sh", "-c", "qstat @torque.farm.particle.cz | grep ' R '"], stdout=subprocess.PIPE).communicate()
    return out.count('\n')



# vi:sw=4:ts=4:et
