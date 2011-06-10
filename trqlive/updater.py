#!/usr/bin/env python

import sys
sys.path.append("../..")
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

from goove.trqlive.models import Node, BatchServer, Subcluster

from xml.dom.minidom import parse, parseString
from optparse import OptionParser, OptionGroup
from xml.parsers.expat import ExpatError

from goove.trqacc.helpers import feedJobsXML,Configuration

import pbs

JOBID_REGEX = re.compile("(\d+-\d+|\d+)\.(.*)")
SUPPORTED_JOB_ATTRS = ['jobid', 'server_id', 'job_owner_id', 'job_gridowner_id', 'cput', 
            'walltime', 'efficiency', 'job_state_id', 'queue_id', 'ctime', 'mtime', 
            'qtime', 'etime', 'start_time', 'comp_time', 'submithost_id', 'exit_status']

VERSION="0.1"

LOG_ERROR=0
LOG_WARNING=1
LOG_INFO=2
LOG_DEBUG=3

Configuration = {
    'loglevel': LOG_DEBUG
}

def log(level, message):
    if level <= Configuration['loglevel']:
        print "<%d> %s" % (level, message)

def attribs_to_dict(attribs):
    """ Convert list of swig attributes
    to a python dictionary """
    return dict([ (x.name,x.value) for x in attribs])


def update_one_node(conn,bs,nodename):
    """
    """
    # TODO
    pass

def update_all_nodes(conn,bs):
    """
    Update all nodes in the database using the given pbs connection conn
    and batch server bs.
    """
    statnodes = pbs.pbs_statnode(conn,"",[],"")
    for sn in statnodes:
        if sn.name.find('.')==-1:
            longname = sn.name+'.'+bs.domainname
        else:
            longname = sn.name
        n,created = Node.objects.get_or_create(name=longname, server=bs)
        if created:
            log(LOG_INFO, "new node will be created: %s" % (longname))
            n.server = bs
            try:
                n.subcluster = Subcluster.objects.get(name=n.name_without_number())
                log(LOG_INFO, "new node will be put in subluster: %s" % (n.subcluster.name))
            except Subcluster.DoesNotExist:
                log(LOG_INFO, "new node will be out of any subcluster: %s" % (longname))
        dattrs = {}
        for a in sn.attribs:
            dattrs[a.name] = a.value
        n.state = dattrs['state']
        log(LOG_INFO, "name: %s, state: %s" % (n.name, n.state))
        n.save()


def update_all_queues(conn,bs):
    """
    Update all queue information in the database using the given pbs connection conn
    and batch server bs.
    """
    # TODO
    pass


def update_all_jobs(conn,bs):
    """
    Update all job information in the database using the given pbs connection conn
    and batch server bs.
    """
    Job.objects.all().delete()
    statjobs = pbs.pbs_statjobs(conn,"",[],"")
    for sj in statjobs:
        j = Job.objects.create(jobid=sj.name.split('.',1)[0], server__name=sj.name.split('.',1)[1])
        da = attribs_to_dict(sj.attribs)
#        for h,jsn in [ x.split('/') for x in da['exec_host'].split('+') ]:
#            j.get
        j.save()




def runAsDaemon():
    """
    Run in daemon mode 
    """
    # TODO: detach from console and log in syslog
    
    for bs in BatchServer.objects.all():
        conn = pbs.pbs_connect(bs.name.encode('iso-8859-1', 'replace'))
        if conn == -1:
            log(LOG_ERROR, "Cannot connect to batch server %s" % bs.name)
            continue
        update_all_nodes(conn,bs)
        


def main():
    usage_string = "%prog [-h] [-l LOGLEVEL] [-n FILE|-j FILE|-e FILE|-s FILE]|[-d DIR] [-r] [-m FILE] [-g FILE] [-t]"
    version_string = "%%prog %s" % VERSION

    opt_parser = OptionParser(usage=usage_string, version=version_string)
    opt_parser.add_option("-l", "--loglevel", type="int", dest="loglevel", default=LOG_WARNING,
        help="Log level (0-3). Default is 0, which means only errors")

    opt_parser.add_option("-s", "--sleep", type="int", dest="sleeptime", default=60,
        help="Number of seconds between two checks of all batch servers. Default is 60 seconds.")

    (options, args) = opt_parser.parse_args()

    if len(args)!=0:
        opt_parser.error("Too many arguments")

    Configuration['loglevel'] = options.loglevel

    runAsDaemon()
        

if __name__=="__main__":
    main()


# vi:ts=4:sw=4:expandtab
