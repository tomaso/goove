#!/usr/bin/env python

# system stuff
import logging,logging.handlers,signal,multiprocessing,os,sys

# Django stuff
os.environ['DJANGO_SETTINGS_MODULE']="settings"
from trqacc.models import BatchServer
import updater_accevents


VERSION = 1
end_children = False

# How this works:
# - fork updating process of accounting for every active batch system
#   - refresh the last update of the accounting for the     
#   - open 
 

def signal_handler(signum, frame):
    global end_children
    logger.info("Signal %d recevied in process %d" % (signum, os.getpid()))
    end_children = True


def main(args, logger):
    global end_children
    if args.file:
        if len(args.batch)>1:
            logger.error("Only one batch server can be specified when processing old log files.")
            sys.exit(-1)
        worker_func = updater_accevents.process_accounting_file
        worker_params = [args.file]
    else:
        worker_func = updater_accevents.proc_func
        worker_params = []

    processes = {}
    logger.debug("Known batch systems: %s" % (str(args.batch)))
    for bsname in args.batch:
        bs = BatchServer.objects.get(name=bsname)
        if bs.isactive:
            logger.info("Starting process for %s" % (bs.name))
            processes[bs] = multiprocessing.Process(target=worker_func, args=worker_params+[bs])
            processes[bs].start()
        else:
            logger.info("Skipping inactive batch system %s" % (bs.name))

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while not end_children:
        for bs,p in processes.items():
            p.join(0.5)
            if not p.is_alive():
                logger.info("Process %s for %d batch system terminated" % (bs.name,p.pid))
                processes.pop(bs)
        if len(processes.keys())==0:
            break

    for bs,p in processes.items():
        p.terminate()
        p.join()


# Inspired by django daemonize code
def daemonize(args, logger, our_home_dir='.', out_log='/dev/null',
              err_log='/dev/null', umask=022):
    # First fork
    try:
        if os.fork() > 0:
            sys.exit(0)     # kill off parent
    except OSError, e:
        logger.critical("fork #1 failed: (%d) %s" % (e.errno, e.strerror))
        sys.exit(1)
    os.setsid()
    os.chdir(our_home_dir)
    os.umask(umask)
    logger.debug("fork #1 succeeded")

    # Second fork
    try:
        if os.fork() > 0:
            os._exit(0)
    except OSError, e:
        logger.critical("fork #2 failed: (%d) %s" % (e.errno, e.strerror))
        os._exit(1)
    logger.debug("fork #2 succeeded")

    si = open('/dev/null', 'r')
    so = open(out_log, 'a+', 0)
    se = open(err_log, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    # Set custom file descriptors so that they get proper buffering.
    sys.stdout, sys.stderr = so, se
    # Write pid to pidfile
    try:
        f = open(args.pid, "wt")
        f.write("%d\n" % os.getpid())
        f.close()
    except IOError, e:
        logger.critical("Cannot write pid file: (%d) %s" % (e.errno, e.strerror))
        os._exit(1)
        
    logger.debug("pid written to %s" % args.pid)

    main(args, logger)


def proc_args_optparse():
    class Args():
        pass
    args = Args()
    
    parser = optparse.OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", help="Log information messages about what is being done.")
    parser.add_option("-d", "--debug", action="store_true", help="Log very verbose debug info.")
    parser.add_option("-n", "--nodetach", action="store_true", help="Do not detach the main process and print log messages to terminal.")
    parser.add_option("-b", "--batch", action="append", help="Hostname of a batch server. The updater gets its info from the database and starts feeding the data from log to the database.")
    parser.add_option("-p", "--pid", action="store", help="Name of the file where the pid of the main process is written.", default="/var/run/goove.pid")
    parser.add_option("-l", "--logfile", action="store", help="Name of the log file.", default=None)
    parser.add_option("-f", "--file", action="store", help="Process this file and quit.", default=None)
    (options, arguments) = parser.parse_args()
    for key in ['verbose', 'debug', 'nodetach']:
        if getattr(options,key):
            setattr(args, key, True)
        else:
            setattr(args, key, False)
    args.batch = options.batch
    args.pid = options.pid
    args.logfile = options.logfile
    args.file = options.file

    return args


def proc_args_argparse():
    parser = argparse.ArgumentParser(description='Start the goove updater daemon.')
    parser.add_argument("-v", "--verbose", action="store_true", help="Log information messages about what is being done.")
    parser.add_argument("-d", "--debug", action="store_true", help="Log very verbose debug info.")
    parser.add_argument("-n", "--nodetach", action="store_true", help="Do not detach the main process and print log messages to terminal.")
    parser.add_argument("-b", "--batch", action="append", help="Hostname of a batch server. The updater gets its info from the database and starts feeding the data from log to the database.")
    parser.add_argument("-p", "--pid", action="store", help="Name of the file where the pid of the main process is written.", default="/var/run/goove.pid")
    parser.add_argument("-l", "--logfile", action="store", help="Name of the log file.", default=None)
    parser.add_argument("-f", "--file", action="store", help="Process this file and quit.", default=None)
    args = parser.parse_args()
    return args
    

if __name__=="__main__":
    if (sys.version_info.major==2 and sys.version_info.minor>=7) or sys.version_info.major==3:
        import argparse
        args = proc_args_argparse()
    else:
        import optparse
        args = proc_args_optparse()

    logger = logging.getLogger("goove_updater")

    if args.logfile:
        handler = logging.FileHandler(args.logfile)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s[%(process)s]: %(levelname)s - %(message)s'))
    elif args.nodetach:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s[%(process)s]: %(levelname)s - %(message)s'))
    else:
        handler = logging.handlers.SysLogHandler(address="/dev/log")
        handler.setFormatter(logging.Formatter('%(name)s[%(process)s]: %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    logger.setLevel(logging.WARNING)
    if args.verbose:
        logger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)


    if args.batch is None:
        logger.error("The batch server must be specified.")
        sys.exit(-1)


    if args.nodetach:
        main(args, logger)
    else:
        daemonize(args, logger)

# vi:ts=4:sw=4:expandtab
