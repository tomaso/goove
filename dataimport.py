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

from django.db.models import Avg, Max, Min, Count

from goove.trq.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, RunningJob, TorqueServer, GridUser, User, Group, JobState, Queue, AccountingEvent

from xml.dom.minidom import parse, parseString
from optparse import OptionParser, OptionGroup
from xml.parsers.expat import ExpatError

from goove.trq.helpers import feedJobsXML,Configuration
from goove.trq.helpers import LOG_ERROR,LOG_WARNING,LOG_INFO,LOG_DEBUG,log
from goove.trq.helpers import getJobState, getQueue, getNode, getTorqueServer, getUser, getGroup, getSubmitHost
from goove.trq.helpers import getRunningCountQstat

import maintenance

JOBID_REGEX = re.compile("(\d+-\d+|\d+)\.(.*)")

VERSION="0.1"

# TODO: make this configurable
last_updatePBSNodes = 0


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
        log(LOG_INFO, "node data saved: %s" % (new_name))

        # Node properties
        new_properties=i.getElementsByTagName("properties")[0].childNodes[0].nodeValue
        n.properties.clear()
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
        n.state.clear()
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

def fixExitStatusLogLine(line,lineno):
    """
    One time helper function. It adds exit_status property to the jobs. 
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
    server,created = getTorqueServer(server_name)
    job,created = Job.objects.get_or_create(jobid=jobid_name, server=server)
    if attrdir.has_key('Exit_status'):
        job.exit_status = int(attrdir['Exit_status'])
        job.save()


    

def parseOneLogLine(line,lineno):
    """
    Parse one line from accounting log and insert the data into DB.
    """
    try:
        date,event,fulljobid,attrs = line.split(';')
    except ValueError:
        log(LOG_WARNING, "skipping invalid line %d: '%s'" % (lineno,line))
        return
        
    log(LOG_DEBUG, "processing accounting line: %s:%s:%s ..." %(date, event, fulljobid))
    # We ignore PBSPro Licensing lines (it is not job related)
    if event=='L':
        log(LOG_DEBUG, "ignored licensing line")
        return

    attrdir = {}
    try:
        for key,val in map(lambda x: x.split('=',1), attrs.split()): 
            attrdir[key] = val
    except ValueError:
        log(LOG_WARNING, "skipping line with invalid attribues %d: '%s'" % (lineno,attrs))

    jobid_name, server_name = JOBID_REGEX.search(fulljobid).groups()
    server,created = getTorqueServer(server_name)
    if created:
        log(LOG_INFO, "new server will be created: %s" % server_name)

    job,created = Job.objects.get_or_create(jobid=jobid_name, server=server)
    if created:
        log(LOG_INFO, "new job will be created: %s.%s" % (jobid_name, server_name))

    if attrdir.has_key('owner'):
        shname = attrdir['owner'].split('@')[1]
        submithost,created = getSubmitHost(shname)
        if created:
            log(LOG_INFO, "new submit host will be created: %s" % shname)
        job.submithost = submithost

    if attrdir.has_key('requestor'):
        shname = attrdir['requestor'].split('@')[1]
        submithost,created = getSubmitHost(shname)
        if created:
            log(LOG_INFO, "new submit host will be created: %s" % shname)
        job.submithost = submithost

    if attrdir.has_key('group'):
        group,created = getGroup(attrdir['group'], server)
        if created:
            log(LOG_INFO, "new group will be created: %s" % attrdir['group'])

    if attrdir.has_key('user'):
        user,created = getUser(attrdir['user'], server, group)
        if created:
            log(LOG_INFO, "new user will be created: %s" % attrdir['user'])
        job.job_owner = user
        job.job_owner.group = group

    if attrdir.has_key('resources_used.cput'):
        h,m,s = attrdir['resources_used.cput'].split(":")
        job.cput = (int(h)*60+int(m))*60+int(s)
    if attrdir.has_key('resources_used.walltime'):
        h,m,s = attrdir['resources_used.walltime'].split(":")
        job.walltime = (int(h)*60+int(m))*60+int(s)
    if attrdir.has_key('resources_used.cput') and attrdir.has_key('resources_used.walltime'):
        if job.walltime!=0:
            job.efficiency = 100*job.cput/job.walltime
        else:
            job.efficiency = 0

    if attrdir.has_key('Exit_status'):
        job.exit_status = int(attrdir['Exit_status'])

    if event=='Q':
        new_state = getJobState('Q')
    elif event=='S' or event=='R' or event=='C' or event=='T':
        new_state = getJobState('R')
    elif event=='E':
        new_state = getJobState('C')
    elif event=='D':
        new_state = getJobState('D')
    elif event=='A':
        new_state = getJobState('A')
    else:
        log(LOG_ERROR, "Unknown event type in accounting log file: %s" % line)
    if job.job_state != getJobState('C'):
#        if new_state == getJobState('R') and job.job_state != getJobState('R'):
#            RunningJob.objects.get_or_create(mainjob=job)
#        elif new_state != getJobState('R') and job.job_state == getJobState('R'):
#            try:
#                rj = RunningJob.objects.get(mainjob=job)
#                rj.delete()
#            except RunningJob.DoesNotExist:
#                pass

        job.job_state = new_state
    else:
        log(LOG_INFO, "Job %s.%s is already finished, not changing the state." % (job.jobid,server.name))
    # running job cache update
        

    if attrdir.has_key('queue'):
        queue,created = getQueue(attrdir['queue'], server)
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
        exec_host_names_slots = attrdir['exec_host'].split('+')
        job.jobslots.clear()

        # convert PBSPro records like 'node1/0*2' to more generic 'node1/0+node1/1'
        exec_host_names_slots_new = []
        for exec_host_name_slot in exec_host_names_slots:
            if exec_host_name_slot.find('*')>=0:
                exec_host_slot0, numslots = exec_host_name_slot.split('*')
                exec_host_name = exec_host_slot0.split('/')[0]
                exec_host_name_slot_new=[ "%s/%d" % (exec_host_name, i) for i in range(0,int(numslots)) ]
                log(LOG_DEBUG, "Exec_host %s converted to %s" % (exec_host_name_slot,exec_host_name_slot_new))
                exec_host_names_slots_new.extend(exec_host_name_slot_new)
            else:
                exec_host_names_slots_new.append(exec_host_name_slot)
        exec_host_names_slots = exec_host_names_slots_new

        for exec_host_name_slot in exec_host_names_slots:
                
            name,slotstr = exec_host_name_slot.split('/')
            slot = int(slotstr)
            node,created = getNode(name, server)
            if created:
                log(LOG_INFO, "new node will be created: node name: %s" % (name))
            js,created = JobSlot.objects.get_or_create(slot=slot,node=node)
            if created:
                log(LOG_INFO, "new jobslot will be created: slot: %d, node name: %s" % (slot,name))
            job.jobslots.add(js)
    job.save()

    d,t = date.split(' ')
    m,d,y = d.split('/')
    ae,created = AccountingEvent.objects.get_or_create(timestamp='%s-%s-%s %s' % (y,m,d,t), type=event, job=job)
    if created:
        log(LOG_INFO, "new accounting event will be created: %s" % ae.timestamp)
        ae.save()
#   This can be used if we are sure that we process
#   new files. We can skip many SELECTs this way
#    ae = AccountingEvent(timestamp='%s-%s-%s %s' % (y,m,d,t), type=event, job=job)
#    log(LOG_INFO, "new accounting event will be created: %s" % ae.timestamp)
#    ae.save()
        

def feedJobsLog(logfile):
    """ Insert data about jobs into database. The data are obtained from text log file
    as described at http://www.clusterresources.com/products/torque/docs/9.1accounting.shtml
    """
    lineno = 0
    for line in logfile:
        lineno += 1
        parseOneLogLine(line, lineno)
#        fixExitStatusLogLine(line, lineno)


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
            try:
                starttime = time.time()
                nodesxml = parseString(out)
                feedNodesXML(nodesxml)
                nodesxml.unlink()
                endtime = time.time()
                log(LOG_INFO, "feedNodesXML() took %f seconds" % (endtime-starttime))
            except ExpatError:
                log(LOG_ERROR, "Cannot parse line: %s" % (out))
            
# TODO: this should be done much less often just to find the Lost jobs
# it is not that useful normally
#            p = subprocess.Popen(["qstat", "-fx", "@%s" % ts.name], stdout=subprocess.PIPE)
#            (out,err) = p.communicate()
#            try:
#                jobsxml = parseString(out)
#                starttime = time.time()
#                feedJobsXML(jobsxml, True)
#                jobsxml.unlink()
#                endtime = time.time()
#                log(LOG_INFO, "feedJobsXML() took %f seconds" % (endtime-starttime))
#            except ExpatError:
#                log(LOG_ERROR, "Cannot parse line: %s" % (out))
            run_qstat = getRunningCountQstat(ts.name)
            run_db = Job.objects.filter(job_state=getJobState('R')).count()
            log(LOG_INFO, "Running jobs:: according to qstat: %d, according to database: %d" % (run_qstat, run_db))
        last_updatePBSNodes = now

def refreshRunningJobs():
    """
    Fill "cache" table with RunningJob - many queries are for running jobs, the table will speed those up
    """
    # TODO: this is an offline operation, we should update RunningJob online as accounting events arrive
    #       but we should do that only when running as daemon, it is useless to do it when parsing old accounting events
    for rj in RunningJob.objects.all():
        rj.jobdelete()
    for rj in Job.objects.filter(job_state__shortname='R'):
        newrj = RunningJob.objects.create(mainjob=rj)
        log(LOG_INFO, "Creating RunningJob: %s for Job: %s" % (newrj, rj))
        newrj.save()
    

def processGridJobMap(gjmfile):
    for l in gjmfile:
        kv = re.findall('"([^="]*)=([^"]*)"', l)
        d = {}
        for k,v in kv:
            d[k] = v
        log(LOG_DEBUG, "gridmap dictionary: %s" % (d))
        if d['lrmsID']=='none' or d['lrmsID']=='FAILED':
            continue
        jobid,tsname = d['lrmsID'].split('.',1)
        try:
            job = Job.objects.get(jobid=jobid, server__name=tsname)
            log(LOG_DEBUG, "job %s found" % str(job))
        except Job.DoesNotExist:
            log(LOG_ERROR, "gridjobmap refers to a job that is not present in database: %s" % (l))
            continue
        griduser,created = GridUser.objects.get_or_create(dn=d['userDN'])
        if created:
            log(LOG_INFO, "new griduser will be created: %s" % (d['userDN']))
        job.job_gridowner = griduser
        job.save()



def main():
    usage_string = "%prog [-h] [-l LOGLEVEL] [-n FILE|-j FILE|-e FILE|-s FILE]|[-d DIR] [-r] [-m FILE] [-g FILE] [-t]"
    version_string = "%%prog %s" % VERSION

    opt_parser = OptionParser(usage=usage_string, version=version_string)
    opt_parser.add_option("-l", "--loglevel", type="int", dest="loglevel", default=LOG_WARNING,
        help="Log level (0-3). Default is 0, which means only errors")
    opt_parser.add_option("-n", "--nodexml", action="append", dest="nodexmlfile", metavar="FILE", 
        help="XML file with node data")
    opt_parser.add_option("-j", "--jobxml", action="append", dest="jobxmlfile", metavar="FILE", 
        help="XML file with job data")
    opt_parser.add_option("-e", "--eventfile", action="append", dest="eventfile", metavar="FILE", 
        help="Text file with event data in accounting log format")
    opt_parser.add_option("-s", "--serverfile", action="append", dest="serverfile", metavar="FILE", 
        help="Text file with server settings (basically output of qmgr `print server` command)")
    opt_parser.add_option("-d", "--daemon", dest="daemondir", metavar="DIR", 
        help="Run in deamon node and read torque accounting logs from DIR")
    opt_parser.add_option("-u", "--updaterj", action="store_true", dest="updateRJ", default=False, 
        help="Update cache table with running jobs from the main jobs table")
    opt_parser.add_option("-g", "--gridjobmap", action="append", dest="gridjobmapfiles", metavar="FILE",
        help="Parse grid-jobmap files so we can find out the grid user for a job")

    oneTimeGroup = OptionGroup(opt_parser, "Maintenance options",
        "Following options are/were handy for one-time fixes in database.")
    oneTimeGroup.add_option("-m", "--mergenodes", action="append", dest="mergenodesfile", metavar="FILE",
        help="Merge nodes according to a file containing only records like 'oldnode=newnode' where all jobs with oldnode will be reattached to newnode. Please note that the new node must be already present in the database with all its jobslots.")
    oneTimeGroup.add_option("-x", "--removeall", action="store_true", dest="removeall", default=False, 
        help="Remove everything from tables (debug option, use with care)")
    oneTimeGroup.add_option("-t", "--deleted", action="store_true", dest="deletedjobs", default=False, 
        help="Walk through all jobs and mark them as deleted if their last accounting record is 'deleted'")
    oneTimeGroup.add_option("-r", "--runevents", action="store_true", dest="runevents", default=False, 
        help="Test if running jobs are not completed in Accounting events log")

    opt_parser.add_option_group(oneTimeGroup)

    (options, args) = opt_parser.parse_args()

    if len(args)!=0:
        opt_parser.error("Too many arguments")

    Configuration['loglevel'] = options.loglevel

    if (options.deletedjobs):
        maintenance.findDeletedJobs()
        return

    if (options.runevents):
        maintenance.checkEventsRunningJobs()
        return

    if (options.gridjobmapfiles):
        for i in options.gridjobmapfiles:
            log(LOG_DEBUG, "Grid job map data will be read from file: %s" % i)
            processGridJobMap(openfile(i))
        return

    if (options.updateRJ):
        refreshRunningJobs()
        return

    if (options.removeall):
        maintenance.removeContent()
        return

    if (options.mergenodesfile):
        for i in options.mergenodesfile:
            log(LOG_DEBUG, "Merge data will be read from file: %s" % i)
            maintenance.mergeNodes(openfile(i))
        return

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
