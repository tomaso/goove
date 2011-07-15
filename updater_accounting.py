# python system stuff
import time,logging,os,signal,traceback,sys,datetime,re

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"

# django stuff
from django.db import transaction, connection

# batch system stuff
import pbs

# goove specific stuff
from goove.trqacc.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, Job, BatchServer, GridUser, User, Group, JobState, Queue, AccountingEvent, SubmitHost
from goove.updater_helpers import getJobState, getQueue, getNode, getUser, getGroup, getSubmitHost, getJobSlot


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


def update_queue(queue, conn):
    """ Update live info about the given queue 
    """
    logger = logging.getLogger("goove_updater")
    statqueues = pbs.pbs_statque(conn, queue.name.encode('iso-8859-1', 'replace') , [], "")
    if len(statqueues)==0:
        logger.error("pbs_statque failes for queue: %s" % queue.name)
    if len(statqueues)>1:
        logger.warning("pbs_statque returned more than one records for queue: %s" % queue.name)

    attr_dict = dict([ (x.name,x.value) for x in statqueues[0].attribs])
    state_count = attr_dict.pop('state_count')
    state_count_dict=dict([('state_count_'+key.lower(),val) for key,val in [tuple(x.split(':')) for x in state_count.strip().split()]])
    attr_dict.update(state_count_dict)
    for key,val in attr_dict.items():
        setattr(queue,key,val)
    logger.debug("queue: %s updated with live info: %s" % (queue.name, attr_dict))
    queue.save()


def update_node(node, conn):
    """ Update live info about the given node 
    """
    logger = logging.getLogger("goove_updater")
    statnodes = pbs.pbs_statnode(conn, node.name.encode('iso-8859-1', 'replace') , [], "")

    

def parse_accounting_line(line, lineno, live_update=False, batch_connection=-1):
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

    job = SQLJob()
    job.jobid = jobid_name
    job.server_id = server.id

    job.refresh_id_jobstate_id()

    if attrdir.has_key('owner'):
        shname = attrdir['owner'].split('@')[1]
        submithost,created = getSubmitHost(shname)
        if created:
            logger.info("new submit host will be created: %s" % shname)
        job.submithost_id = submithost.pk

    if attrdir.has_key('requestor'):
        shname = attrdir['requestor'].split('@')[1]
        submithost,created = getSubmitHost(shname)
        if created:
            logger.info("new submit host will be created: %s" % shname)
        job.submithost_id = submithost.id

    if attrdir.has_key('group'):
        group,created = getGroup(attrdir['group'], server)
        if created:
            logger.info("new group will be created: %s" % attrdir['group'])

    if attrdir.has_key('user'):
        user,created = getUser(attrdir['user'], server, group)
        if created:
            logger.info("new user will be created: %s" % attrdir['user'])
        job.job_owner_id = user.id
        # TODO: convert this to direct SQL as well
        user.group = group

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
    elif event=='G':
        new_state = getJobState('D')
    else:
        logger.error("Unknown event type in accounting log file: %s" % line)
        return
    if job.job_state_id != getJobState('C').id:
        job.job_state_id = new_state.id
    else:
        logger.info("Job %s.%s is already finished, not changing the state." % (job.jobid,server.name))

    if attrdir.has_key('queue'):
        queue,created = getQueue(attrdir['queue'], server)
        if created:
            logger.info("new queue will be created: %s" % attrdir['queue'])
        job.queue_id = queue.id
        if live_update:
            update_queue(queue, batch_connection)

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
        job.jobslots = []

        # convert PBSPro records like 'node1/0*2' to more generic 'node1/0+node1/1'
        exec_host_names_slots_new = []
        for exec_host_name_slot in exec_host_names_slots:
            if exec_host_name_slot.find('*')>=0:
                exec_host_slot0, numslots = exec_host_name_slot.split('*')
                exec_host_name = exec_host_slot0.split('/')[0]
                exec_host_name_slot_new=[ "%s/%d" % (exec_host_name, i) for i in range(0,int(numslots)) ]
                logger.debug("Exec_host %s converted to %s" % (exec_host_name_slot,exec_host_name_slot_new))
                exec_host_names_slots_new.extend(exec_host_name_slot_new)
            else:
                exec_host_names_slots_new.append(exec_host_name_slot)
        exec_host_names_slots = exec_host_names_slots_new

        for exec_host_name_slot in exec_host_names_slots:
                
            name,slotstr = exec_host_name_slot.split('/')
            slot = int(slotstr)
            node,created = getNode(name, server)
            if created:
                logger.info("new node will be created: node name: %s" % (name))
                node.save()
            js,created = getJobSlot(slot=slot,node=node)
            if created:
                logger.info("new jobslot will be created: slot: %d, node name: %s" % (slot,name))
                js.save()
            job.jobslots.append(js.id)
    job.save()


    if job.id == -1:
        job.refresh_id_jobstate_id()
    d,t = date.split(' ')
    m,d,y = d.split('/')
    timestamp='%s-%s-%s %s' % (y,m,d,t)
    cursor.execute("INSERT IGNORE INTO trqacc_accountingevent (timestamp, type, job_id) VALUES (%s,%s,%s)", [timestamp, event, job.id])

    
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
        logger.info("Last processed accounting event is unknown or too old, trying to update it")
        update_lastacc(server)

    today_filename = get_today_filename(server.accountingdir)

    if not server.lastacc_update:
        filename = find_oldest_file(server.accountingdir)
    else:
        filename = get_filename_date(server.accountingdir,server.lastacc_update)
        
    while filename!=today_filename:
        process_accounting_file(filename)
        filename = get_nextday_filename(server.accountingdir, filename)
        
    
    batch_connection = pbs.pbs_connect(server.name.encode('iso-8859-1', 'replace'))
    if batch_connection==-1:
        logger.error("Cannot connect to %s - live data will be missing" % server.name)

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
                    time.sleep(10)
                    fd.close()
                    save_server_lasttime()
                    transaction.commit()
                    filename = get_today_filename(server.accountingdir)
                    logger.info("The date has changed - switching to new file: %s" % filename)
                    fd = open_or_exit(filename)
            else:
                lineno += 1
                logger.info("Processing line number %d" % lineno)
                if batch_connection==-1:
                    parse_accounting_line(l, lineno)
                else:
                    parse_accounting_line(l, lineno, True, batch_connection)
                if (lineno % 20)==0:
                    transaction.commit()
    except BaseException, e:
        raise e
    finally:
        transaction.commit()


# vi:ts=4:sw=4:expandtab
