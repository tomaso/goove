# python system stuff
import time,logging,os,signal,traceback,sys,datetime,re

os.environ['DJANGO_SETTINGS_MODULE']="settings"

# django stuff
from django.db import transaction, connection

# goove specific stuff
from trqacc.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, BatchServer, GridUser, User, Group, JobState, Queue, AccountingEvent, SubmitHost, LiveJob, EventAttribute
from updater_helpers import getJobState, getQueue, getNode, getUser, getGroup, getSubmitHost, getJobSlot, getEventAttribute


JOBID_REGEX = re.compile("(\d+-\d+|\d+)\.(.*)")
SUPPORTED_JOB_ATTRS = ['jobid', 'server_id', 'job_owner_id', 'job_gridowner_id', 'cput', 
            'walltime', 'efficiency', 'job_state_id', 'queue_id', 'ctime', 'mtime', 
            'qtime', 'etime', 'start_time', 'comp_time', 'submithost_id', 'exit_status']


class SQLJob:
    def refresh_id_jobstate_id(self):
        """ 
        Refresh id from the database. Sets id to -1 if the job is not present.
        jobid and server_id must be set.
        """
        cursor = connection.cursor()
        if(cursor.execute("SELECT id,job_state_id FROM trqacc_job WHERE jobid=%s AND server_id=%s", [self.jobid,self.server_id])==0):
            self.id = -1
            self.job_state_id = -1
        else:
            row = cursor.fetchone()
            self.id = row[0]
            self.job_state_id = row[1]
        
    def save(self):
        logger = logging.getLogger("goove_updater")
        cursor = connection.cursor()
        attrs = [a for a in SUPPORTED_JOB_ATTRS if hasattr(self,a)]
        if self.id == -1:
            logger.debug("new job will be created")
            sqlkeys = ",".join(attrs)
            sqlvalues = '%s,'*(len(attrs)-1) + '%s'
            cursor.execute("INSERT INTO trqacc_job (%s) VALUES (%s)" % (sqlkeys,sqlvalues), 
                [getattr(self,x) for x in attrs]
            )
        else:
            logger.debug("the updated job id: %d" % self.id)
            sqlitems = ",".join([("%s=%%s" % i) for i in attrs])
            cursor.execute("UPDATE trqacc_job SET %s WHERE id=%d" % (sqlitems,self.id), 
                [getattr(self,x) for x in attrs]
            )
        # Save jobslots data if it is present
        if hasattr(self,'jobslots'):
            # TODO: This query can be very slow - I don't know how to do it better now
            j = Job.objects.get(server__pk=self.server_id,jobid=self.jobid)
            job_id = j.id

            for jobslot_id in self.jobslots:
                cursor.execute("INSERT IGNORE INTO trqacc_job_jobslots (job_id,jobslot_id) VALUES (%d,%d)" % (job_id, jobslot_id))


def save_server_lasttime():
    global server,last_event_time
    if server.lastacc_update < last_event_time:
        server.lastacc_update = last_event_time
        server.save()


def signal_handler(signum, frame):
    logger = logging.getLogger("goove_updater")
    logger.info("Signal %d recevied in accounting subprocess %d" % (signum, os.getpid()))
    save_server_lasttime()
    sys.exit(signum)


def update_lastacc(server):
    if AccountingEvent.objects.filter(job__server=server).count() < 1:
        return
    last = AccountingEvent.objects.filter(job__server=server).order_by('-timestamp')[0]
    server.lastacc_update = last.timestamp
    server.save()


# TODO: this should be more smart 
def find_oldest_file(server):
    ol = server.accountingdir+"/"+os.listdir(server.accountingdir).sort()[0]
    logging.getLogger("goove_updater").info("Found oldest accounting log file: %s" % ol)
    return ol


def get_filename_date(logdir, d):
    """ Return accounting log filename for given datetime
    """
    return ("%s/%d%02d%02d" % (logdir,d.year,d.month,d.day))


def get_today_filename(logdir):
    """ Get the today's file in given directory
    """
    d=datetime.datetime.today()
    return get_filename_date(logdir, d)


def get_nextday_filename(logdir, filename):
    """ Return accounting log filename for the next day
    """
    fn = os.path.basename(filename)
    d = datetime.datetime(int(fn[:4]),int(fn[4:6]),int(fn[6:]))+datetime.timedelta(days=1)
    return get_filename_date(logdir, d)


def open_or_exit(filename):
    try:
        fd = open(filename)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger = logging.getLogger("goove_updater")
        for l in traceback.format_exception(exc_type, exc_value, exc_traceback):
            logger.critical(l)
        sys.exit(-1)
    return fd


def parse_accounting_line(line, lineno):
    """ Parse one line from accounting log and insert the data into DB.
    """
    global server,last_event_time

    logger = logging.getLogger("goove_updater")
    cursor = connection.cursor()
    try:
        date,event,fulljobid,attrs = line.split(';')
    except ValueError:
        logger.warning("skipping invalid line %d: '%s'" % (lineno,line))
        return
        
    logger.debug("Processing accounting line: %s:%s:%s ..." %(date, event, fulljobid))
    last_event_time = datetime.datetime.strptime(date, "%m/%d/%Y %H:%M:%S")
    if last_event_time < server.lastacc_update:
        logger.info("Ignoring accounting event with datetime %s" % str(last_event_time))
        return
    # We ignore PBSPro Licensing lines (it is not job related)
    if event=='L':
        logger.debug("Ignoring licensing line")
        return

    attrdir = {}
    try:
        for key,val in map(lambda x: x.split('=',1), attrs.split()): 
            attrdir[key] = val
    except ValueError:
        logger.warning("Skipping line with invalid attribues %d: '%s'" % (lineno,attrs))

    jobid_name, server_name = JOBID_REGEX.search(fulljobid).groups()
    if server_name!=server.name:
        logger.warning("The name of the server in jobid: %s differs from server name in database: %s" % (server_name,server.name))

    d,t = date.split(' ')
    m,d,y = d.split('/')
    timestamp='%s-%s-%s %s' % (y,m,d,t)
    cursor.execute("INSERT IGNORE INTO trqacc_accountingevent (timestamp, type, short_jobid, server_id) VALUES (%s,%s,%s)", [timestamp, event, jobid_name, server.id])
    cursor.execute("SELECT LAST_INSERT_ID()")
    row = cursor.fetchone()
    ae_id = row[0]

    # already existing accounting event?
    if ae_id > 0:
        for key,val in attrdir.items():
            ea,created = getEventAttribute(key)
            cursor.execute("INSERT INTO trqacc_eventattributevalue (ae_id, ea_id, value) VALUES (%s,%s,%s)", [ae_id, ea.id, val])

    
@transaction.commit_manually
def process_accounting_file(filename):
    logger = logging.getLogger("goove_updater")
    logger.info("process_accounting_file: opening file %s" % (filename))
    transaction.commit()
    fd = open_or_exit(filename)
    lineno = 0
    try:
        for l in fd:
            lineno += 1
            parse_accounting_line(l, lineno)
            if (lineno % 1000)==0:
                save_server_lasttime()
                transaction.commit()
    except BaseException, e:
        logger.warning("%s" % (traceback.format_exc()))
        for l in traceback.format_exception(exc_type, exc_value, exc_traceback):
            logger.critical(l)
        raise e
    finally:
        transaction.commit()



@transaction.commit_manually
def proc_func(_server):
    global server,last_event_time
    server = _server

    logger = logging.getLogger("goove_updater")
    logger.info("New process for accounting from server %s started with pid %d." % (server.name, os.getpid()))
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Last processed accounting event for %s is %s" % (server.name,server.lastacc_update))

    now = datetime.datetime.now()
    if not server.lastacc_update or (now-server.lastacc_update).days>=1:
        # this usually means that the update process did not update the lastacc_update
        # properly, so before we process the old accounting events, we make sure
        # the lastacc_update is correct
        logger.info("Last processed accounting event is unknown or too old, trying to update it - this may take a while")
        update_lastacc(server)

    today_filename = get_today_filename(server.accountingdir)

    if not server.lastacc_update:
        filename = find_oldest_file(server.accountingdir)
    else:
        filename = get_filename_date(server.accountingdir,server.lastacc_update)
        
    while filename!=today_filename:
        process_accounting_file(filename)
        filename = get_nextday_filename(server.accountingdir, filename)
        
    
    fd = open_or_exit(filename)
    lineno = 0
    last_event_time = server.lastacc_update
    try:
        while True:
            l = fd.readline()
            if l == '':
                if get_today_filename(server.accountingdir)==filename:
                    time.sleep(1)
                else:
                    fd.close()
                    save_server_lasttime()
                    transaction.commit()
                    filename = get_today_filename(server.accountingdir)
                    logger.info("The date has changed - switching to new file: %s" % filename)
                    while not os.path.exists(filename):
                        logger.info("The file %s does not exist. Waiting for its presence ..." % filename)
                        time.sleep(10)
                    fd = open_or_exit(filename)
            else:
                lineno += 1
                logger.info("Processing line number %d" % lineno)
                parse_accounting_line(l, lineno)
                if (lineno % 20)==0:
                    save_server_lasttime()
                    transaction.commit()
    except BaseException, e:
        raise e
    finally:
        transaction.commit()


# vi:ts=4:sw=4:expandtab
