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
from goove.trq.models import Job
from goove.trq.models import TorqueServer
from goove.trq.models import User
from goove.trq.models import JobState
from goove.trq.models import Queue

from xml.dom.minidom import parse, parseString
from optparse import OptionParser


LOG_ERROR=0
LOG_WARNING=1
LOG_INFO=2
LOG_DEBUG=3

VERSION="0.1"

loglevel = 0


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

def feedNodesXML(x):
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

def feedJobsXML(x):
    jobid_regex = re.compile("(\d+)\.(.*)")

    for i in x.childNodes[0].childNodes:
        new_full_jobid = i.getElementsByTagName("Job_Id")[0].childNodes[0].nodeValue
        new_jobid_name, new_server_name = jobid_regex.search(new_full_jobid).groups()

        new_server,created = TorqueServer.objects.get_or_create(name=new_server_name)
        if created:
            log(LOG_INFO, "new server will be created: %s" % new_server_name)

        new_job,created = Job.objects.get_or_create(jobid=int(new_jobid_name), server=new_server)
        if created:
            log(LOG_INFO, "new job will be created: %s" % new_jobid_name)
        else:
            log(LOG_INFO, "job already exists (will only update data): %s" % new_jobid_name)

        # used resources
        restag = i.getElementsByTagName("resources_used")[0]
        # cput
        new_cput_string = restag.getElementsByTagName("cput")[0].childNodes[0].nodeValue
        h,m,s = new_cput_string.split(":")
        new_job.cput = (int(h)*60+int(m))*60+int(s)
        # walltime
        new_walltime_string = restag.getElementsByTagName("walltime")[0].childNodes[0].nodeValue
        h,m,s = new_walltime_string.split(":")
        new_job.walltime = (int(h)*60+int(m))*60+int(s)

        new_job_owner_name = i.getElementsByTagName("Job_Owner")[0].childNodes[0].nodeValue
        new_job_owner_name = new_job_owner_name.split("@")[0]
        new_job_owner,created = User.objects.get_or_create(name=new_job_owner_name)
        if created:
            log(LOG_INFO, "new user will be created: %s" % new_job_owner_name)

        new_job.job_owner = new_job_owner

        # TODO: fill the rest

        new_job.save()

def feedJobsLog(logfile):
    """ Insert data about jobs into database. The data are obtained from text log file
    as described at http://www.clusterresources.com/products/torque/docs/9.1accounting.shtml
    """
    for line in logfile():
        date,event,fulljobid,attrs = line.split(';')
        if event=='Q':
        elif event=='S':
        elif event=='E':
        elif event=='D':
        else:
            log(LOG_ERROR, "Unknown event type in accounting log file")
    


def BatchServerInit(servername):
    """ Static stuff for golias farm. Added at the beginning for testing purposes """
    TorqueServer(name=servername).save()



def main():
    global loglevel

    usage_string = "%prog [-h] [-l LOGLEVEL] [-n FILE|-j FILE|-e FILE]|[-d DIR]"
    version_string = "%%prog %s" % VERSION

    opt_parser = OptionParser(usage=usage_string, version=version_string)
    opt_parser.add_option("-l", "--loglevel", type="int", dest="loglevel", help="Log level (0-3). Default is 0, which means only errors", default=0)
    opt_parser.add_option("-n", "--nodexml", action="append", dest="nodexmlfile", metavar="FILE", help="XML file with node data")
    opt_parser.add_option("-j", "--jobxml", action="append", dest="jobxmlfile", metavar="FILE", help="XML file with job data")
    opt_parser.add_option("-e", "--eventfile", action="append", dest="eventfile", metavar="FILE", 
        help="Text file with event data in accunting log format")
    opt_parser.add_option("-d", "--daemon", dest="daemon", metavar="DIR", 
        help="Run in deamon node and read torque accounting logs from DIR")
    opt_parser.add_option("-s", "--server", dest="server", metavar="BATCHSERVER", 
        help="Name of the first batch server to be inserted in the database")

    (options, args) = opt_parser.parse_args()

    print options

    if len(args)!=0:
        opt_parser.error("Too many arguments")

    loglevel = options.loglevel

    return

    # invalid combinations
    if (options.nodexmlfile or options.jobxmlfile or options.eventfile) and options.daemon:
        opt_parser.error("You cannot run as daemon and process data files at once. Choose only one mode of running.")
    if not (options.nodexmlfile or options.jobxmlfile or options.eventfile or options.daemon):
        opt_parser.error("Mode of running is missing. Please specify one of -n, -j -e or -d.")

    if options.server:
        BatchServerInit(options.server)

    if options.nodexmlfile:
        for i in options.nodexmlfile:
            nodesxml = parse(i)
            feednodesXML(nodesxml)

    if options.jobxmlfile:
        for i in options.jobxmlfile:
            jobsxml = parse(i)
            feedJobsXML(jobsxml)

    if options.eventfile:
        for i in options.eventfile:
            logfile = file(i, "r")
            feedJobsLog(logfile)
        
    
if __name__=="__main__":

    main()


# vi:ts=4:sw=4:expandtab
