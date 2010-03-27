#!/usr/bin/env python

import sys
sys.path.append("..")
import goove
import os
import os.path
import datetime
import time
import bz2
import gzip
import subprocess

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"

import re

from goove.trq.models import Node
from goove.trq.models import NodeProperty
from goove.trq.models import NodeState
from goove.trq.models import SubCluster
from goove.trq.models import Job
from goove.trq.models import TorqueServer
from goove.trq.models import User
from goove.trq.models import JobState
from goove.trq.models import Queue
from goove.trq.models import AccountingEvent

from xml.dom.minidom import parse, parseString
from optparse import OptionParser


LOG_ERROR=0
LOG_WARNING=1
LOG_INFO=2
LOG_DEBUG=3
JOBID_REGEX = re.compile("(\d+)\.(.*)")

VERSION="0.1"

# TODO: make this configurable
loglevel = LOG_WARNING
last_updatePBSNodes = 0


def log(level, message):
    if level <= loglevel:
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
    for j in Job.objects.all():
        j.delete()
#   Job states are inserted initially from initial_data.json
#    for js in JobState.objects.all():
#        js.delete()
    for q in Queue.objects.all():
        q.delete()
    for u in User.objects.all():
        u.delete()

def feedNodesXML(x):
    sc_regex = re.compile("(\D+)")

    for i in x.childNodes[0].childNodes:
        new_name=i.getElementsByTagName("name")[0].childNodes[0].nodeValue
        n, created = Node.objects.get_or_create(name=new_name)
        if created:
            log(LOG_INFO, "new node will be created: %s" % (new_name))

        # np
        new_np=int(i.getElementsByTagName("np")[0].childNodes[0].nodeValue)
        n.np = new_np

        # Node's subcluster
        sc_name = sc_regex.search(new_name).groups()[0]
        sc, created = SubCluster.objects.get_or_create(name=sc_name)
        if created:
            log(LOG_INFO, "new subcluster saved: %s" % (sc_name))
        n.subcluster = sc

        n.save()
        log(LOG_INFO, "new node saved: %s" % (new_name))

        # Node properties
        new_properties=i.getElementsByTagName("properties")[0].childNodes[0].nodeValue
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
        new_states=i.getElementsByTagName("state")[0].childNodes[0].nodeValue
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

def feedJobsXML(x):
    """
    Parse xml produces by pbsnodes -[a]x and feed the data into django
    data structures.
    """
    JOBID_REGEX = re.compile("(\d+)\.(.*)")

    updated_jobs = []

    for i in x.childNodes[0].childNodes:
        new_full_jobid = i.getElementsByTagName("Job_Id")[0].childNodes[0].nodeValue
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
        
        # mtime
        new_walltime_string = restag.getElementsByTagName("walltime")[0].childNodes[0].nodeValue
        h,m,s = new_walltime_string.split(":")
        new_job.walltime = (int(h)*60+int(m))*60+int(s)
        
        new_job.save()
        updated_jobs.append(new_job)
    # check that not finished jobs are between recently updated jobs
    # otherwise it is kinda lost job
    for j in Job.objects.exclude(job_state__shortname="C"):
        if j not in updated_jobs:
            log(LOG_WARNING, "job %d.%s is in database unfinished but not present in torque anymore" % (j.jobid, j.server.name))
            

def parseOneLogLine(line,lineno):
    """
    Parse one line from accounting log and insert the date into DB.
    """
    try:
        date,event,fulljobid,attrs = line.split(';')
    except ValueError:
        log(LOG_WARNING, "skipping invalid line %d: '%s'" % (lineno,line))
        return
        
    log(LOG_DEBUG, "processing accounting line: %s:%s:%s ..." %(date, event, fulljobid))
    attrdir = {}
    try:
        for key,val in map(lambda x: x.split('=',1), attrs.split()): 
            attrdir[key] = val
    except ValueError:
        log(LOG_WARNING, "skipping line with invalid attribues %d: '%s'" % (lineno,attrs))
        
    jobid_name, server_name = JOBID_REGEX.search(fulljobid).groups()
    server,created = TorqueServer.objects.get_or_create(name=server_name)
    if created:
        log(LOG_INFO, "new server will be created: %s" % server_name)
    job,created = Job.objects.get_or_create(jobid=int(jobid_name), server=server)
    if created:
        log(LOG_INFO, "new job will be created: %s.%s" % (jobid_name, server_name))

    if attrdir.has_key('user'):
        user,created = User.objects.get_or_create(name=attrdir['user'])
        if created:
            log(LOG_INFO, "new user will be created: %s" % attrdir['user'])
        job.job_owner = user
    if attrdir.has_key('resources_used.cput'):
        h,m,s = attrdir['resources_used.cput'].split(":")
        job.cput = (int(h)*60+int(m))*60+int(s)
    if attrdir.has_key('resources_used.walltime'):
        h,m,s = attrdir['resources_used.walltime'].split(":")
        job.walltime = (int(h)*60+int(m))*60+int(s)
    if event=='Q':
        job.job_state = JobState.objects.get(shortname='Q')
    elif event=='S' or event=='R' or event=='C' or event=='T':
        job.job_state = JobState.objects.get(shortname='R')
    elif event=='E' or event=='D' or event=='A':
        job.job_state = JobState.objects.get(shortname='C')
    else:
        log(LOG_ERROR, "Unknown event type in accounting log file: %s" % line)
    if attrdir.has_key('queue'):
        queue,created = Queue.objects.get_or_create(name=attrdir['queue'])
        if created:
            log(LOG_INFO, "new queue will be created: %s" % attrdir['queue'])
        job.queue = queue
    if attrdir.has_key('ctime'):
        job.ctime = datetime.datetime.fromtimestamp(int(attrdir['ctime']))
    if attrdir.has_key('mtime'):
        job.mtime = datetime.datetime.fromtimestamp(int(attrdir['mtime']))
    if attrdir.has_key('qtime'):
        job.qtime = datetime.datetime.fromtimestamp(int(attrdir['qtime']))
    if attrdir.has_key('etime'):
        job.etime = datetime.datetime.fromtimestamp(int(attrdir['etime']))
    if attrdir.has_key('start'):
        job.start_time = datetime.datetime.fromtimestamp(int(attrdir['start']))
    if attrdir.has_key('end'):
        job.comp_time = datetime.datetime.fromtimestamp(int(attrdir['end']))
    if attrdir.has_key('exec_host'):
        exec_host_name = attrdir['exec_host'].split("/",1)[0]
        exec_host,created = Node.objects.get_or_create(name=exec_host_name)
        if created:
            log(LOG_INFO, "new node (exec_host) will be created: %s" % exec_host_name)
        job.exec_host = exec_host
    job.save()

    # TODO: what if we are parsing the same file again?
    d,t = date.split(' ')
    m,d,y = d.split('/')
    ae,created = AccountingEvent.objects.get_or_create(timestamp='%s-%s-%s %s' % (y,m,d,t), type=event, job=job)
    if created:
        log(LOG_INFO, "new account event will be created: %s" % ae.timestamp)
    ae.save()


def feedJobsLog(logfile):
    """ Insert data about jobs into database. The data are obtained from text log file
    as described at http://www.clusterresources.com/products/torque/docs/9.1accounting.shtml
    """
    lineno = 0
    for line in logfile:
        lineno += 1
        parseOneLogLine(line, lineno)


def openfile(filename):
    """
    Guess file type, open it appropriately
    and return file handle
    """
    ending = os.path.basename(filename).split('.')[-1]
    log(LOG_INFO, "filename: %s, ending: %s" % (filename, ending))
    if ending=="bz2":
        log(LOG_INFO, "opening file as bz2")
        return bz2.BZ2File(filename)
    elif ending=="gz":
        log(LOG_INFO, "opening file as gzip")
        return gzip.GzipFile(filename)
    else:
        return open(filename, "r")


def getTodayFile(logdir):
    """
    Get the today's file in given directory
    """
    d=datetime.datetime.today()
    return ("%d%02d%02d" % (d.year,d.month,d.day))
    

def runAsDaemon(logdir):
    """
    Monitor last file in logdir in format YYYYMMDD for appended lines and switch to new one
    if it appears.
    """
    filename = os.path.join(logdir, getTodayFile(logdir))
    log(LOG_INFO, "Starting as daemon, opening file %s" % filename)
    f = openfile(filename)
    if not f:
        log(LOG_ERROR, "Unable to open file %s" % filename)
        sys.exit(-1)
    lineno = 0
    while True:
        lineno += 1
        line = f.readline() 
        if line=='':
            time.sleep(5)
            newfilename = os.path.join(logdir, getTodayFile(logdir))
            if newfilename != filename:
                filename = newfilename
                log(LOG_INFO, "Last file changed, opening file %s" % filename)
                f = openfile(filename) 
                if not f:
                    log(LOG_ERROR, "Unable to open file %s" % filename)
                    sys.exit(-1)
            updatePBSNodes()
        else:
            parseOneLogLine(line, lineno)
        
# BIG TODO: this should be configurable (see parsing ini files)
def updatePBSNodes():
    """
    Get pbsnodes info from torque server once in a while and update the info
    """
    global last_updatePBSNodes
    updatePBSNodes_interval = 600
    now = int(time.time())
    log(LOG_INFO, "pbsnodes data check, last: %d, now: %d" % (last_updatePBSNodes, now))
    if now - last_updatePBSNodes > updatePBSNodes_interval:
        log(LOG_INFO, "pbsnodes data outdated - getting new")
        for ts in TorqueServer.objects.all():
            log(LOG_INFO, "pbsnodes data outdated - getting new for %s" % ts.name)
            # TODO: timeout after 1min
            p = subprocess.Popen(["pbsnodes", "-ax", "-s", ts.name], stdout=subprocess.PIPE)
            (out,err) = p.communicate()
            jobsxml = parseString(out)
            feedNodesXML(jobsxml)
        last_updatePBSNodes = now
    

def main():
    global loglevel

    usage_string = "%prog [-h] [-l LOGLEVEL] [-n FILE|-j FILE|-e FILE|-s FILE]|[-d DIR]"
    version_string = "%%prog %s" % VERSION

    opt_parser = OptionParser(usage=usage_string, version=version_string)
    opt_parser.add_option("-l", "--loglevel", type="int", dest="loglevel", help="Log level (0-3). Default is 0, which means only errors", default=0)
    opt_parser.add_option("-n", "--nodexml", action="append", dest="nodexmlfile", metavar="FILE", help="XML file with node data")
    opt_parser.add_option("-j", "--jobxml", action="append", dest="jobxmlfile", metavar="FILE", help="XML file with job data")
    opt_parser.add_option("-e", "--eventfile", action="append", dest="eventfile", metavar="FILE", 
        help="Text file with event data in accunting log format")
    opt_parser.add_option("-s", "--serverfile", action="append", dest="serverfile", metavar="FILE", 
        help="Text file with server settings (basically output of qmgr `print server` command)")
    opt_parser.add_option("-d", "--daemon", dest="daemondir", metavar="DIR", 
        help="Run in deamon node and read torque accounting logs from DIR")

    (options, args) = opt_parser.parse_args()

    if len(args)!=0:
        opt_parser.error("Too many arguments")

    loglevel = options.loglevel

    # invalid combinations
    if (options.nodexmlfile or options.jobxmlfile or options.eventfile or options.serverfile) and options.daemondir:
        opt_parser.error("You cannot run as daemon and process data files at once. Choose only one mode of running.")
    if not (options.nodexmlfile or options.jobxmlfile or options.eventfile or options.serverfile or options.daemondir):
        opt_parser.error("Mode of running is missing. Please specify one of -n, -j -e -s or -d.")

    if options.eventfile:
        for i in options.eventfile:
            log(LOG_DEBUG, "opening file %s" % i)
            feedJobsLog(openfile(i))
        
    if options.nodexmlfile:
        for i in options.nodexmlfile:
            nodesxml = parse(openfile(i))
            feedNodesXML(nodesxml)

    if options.jobxmlfile:
        for i in options.jobxmlfile:
            jobsxml = parse(openfile(i))
            feedJobsXML(jobsxml)
    
    if options.serverfile:
        log(LOG_ERROR, "Server file parsing is not supported yet")
        sys.exit(-1)

    if options.daemondir:
        runAsDaemon(options.daemondir)
        

    
if __name__=="__main__":
    main()


# vi:ts=4:sw=4:expandtab
