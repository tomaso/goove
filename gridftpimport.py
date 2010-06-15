#!/usr/bin/env python

import sys
sys.path.append("..")

import os
import os.path
import bz2
import gzip

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"

from goove.gridftp.models import UnixUser
from goove.gridftp.models import GridUser
from goove.gridftp.models import ClientNode
from goove.gridftp.models import ServerNode
from goove.gridftp.models import Transfer

from optparse import OptionParser
import re
import time


LOG_ERROR=0
LOG_WARNING=1
LOG_INFO=2
LOG_DEBUG=3
VERSION=1

loglevel = LOG_WARNING

def log(level, message):
    if level <= loglevel:
        print "<%d> %s" % (level, message)

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

def processDPMLogFile(logfile, servernodename):
    re.findall('"([^="]*)=([^"]*)"', l)


def processLogFile(logfile, servernodename):
    """ The main function that does the log parsing """
    regex_line = re.compile("\[(?P<pid>\d+)\](?P<date>.*) :: (?P<message>.*)")
    regex_conn = re.compile("New connection from: (?P<host>.*):(?P<port>\d+)")
    regex_dn = re.compile("DN (?P<dn>.*) successfully authorized.")
    regex_user = re.compile("User (?P<user>.*) successfully authorized.")
    regex_stor = re.compile("(?P<host>.*):(?P<port>\d+): \[CLIENT\]: STOR (?P<file>.*)")
    regex_retr = re.compile("(?P<host>.*):(?P<port>\d+): \[CLIENT\]: RETR (?P<file>.*)")
    opentransfers = {}
    servernode,created = ServerNode.objects.get_or_create(name=servernodename)
    for line in logfile:
        mo=regex_line.match(line)
        if not mo:
            continue

        if mo.group('message') == 'Server started in inetd mode.':
            log(LOG_DEBUG, "New transfer, pid: %s" % mo.group('pid'))
            t = Transfer()
            t.servernode = servernode
            opentransfers[mo.group('pid')] = t
            t.start_time = time.strftime("%F %T", time.strptime(mo.group('date').strip(), '%a %b %d %H:%M:%S %Y'))
            continue

        if mo.group('message').startswith('Closed connection from'):
            log(LOG_DEBUG, "Ending transfer, pid: %s" % mo.group('pid'))
            t = opentransfers.pop(mo.group('pid'))
            t.comp_time = time.strftime("%F %T", time.strptime(mo.group('date').strip(), '%a %b %d %H:%M:%S %Y'))

            # currently we support only STOR and RETR actions
            if t.type=='RETR' or t.type=='STOR':
                t.save()
            continue

        moconn = regex_conn.match(mo.group('message'))
        if moconn:
            t.clientnode,created = ClientNode.objects.get_or_create(name=moconn.group('host'))
            t.port = moconn.group('port')
            log(LOG_DEBUG, "Transfer client node: %s" % t.clientnode)
            continue
        modn = regex_dn.match(mo.group('message'))
        if modn:
            t.griduser,created = GridUser.objects.get_or_create(dn=modn.group('dn'))
            log(LOG_DEBUG, "Transfer DN: %s" % t.griduser)
            continue
        mouser = regex_user.match(mo.group('message'))
        if mouser:
            t.unixuser,created = UnixUser.objects.get_or_create(name=mouser.group('user'))
            log(LOG_DEBUG, "Transfer user: %s" % t.unixuser)
            continue
        mostor = regex_stor.match(mo.group('message'))
        if mostor:
            t.type = 'STOR'
            t.file = mostor.group('file')
            log(LOG_DEBUG, "Transfer type: %s" % t.type)
            continue
        moretr = regex_retr.match(mo.group('message'))
        if moretr:
            t.type = 'RETR'
            t.file = moretr.group('file')
            log(LOG_DEBUG, "Transfer type: %s" % t.type)
            continue

        		

def main():
    global loglevel
    usage_string = "%prog -f FILE"
    version_string = "%%prog %s" % VERSION
    opt_parser = OptionParser(usage=usage_string, version=version_string)
    opt_parser.add_option("-l", "--loglevel", type="int", dest="loglevel", default=0,
        help="Log level (0-3). Default is 0, which means only errors")
    opt_parser.add_option("-f", "--logfile", action="append", dest="logfile", metavar="FILE", 
        help="Log text file with transfer data.")
    opt_parser.add_option("-n", "--servernode", action="append", dest="servernodename", metavar="FQDN", 
        help="Server node that produced the given log")

    (options, args) = opt_parser.parse_args()

    if len(args)!=0:
        opt_parser.error("Too many arguments")

    loglevel = options.loglevel

    if options.logfile:
        for i in options.logfile:
            log(LOG_DEBUG, "opening file %s" % i)
            processLogFile(openfile(i), options.servernodename[0])


if __name__=="__main__":
    main()


# vi:ts=4:sw=4:expandtab
