#!/usr/bin/env python

# system stuff
import argparse,logging,logging.handlers,signal,multiprocessing,os,sys,lockfile

# in OpenSUSE this is in package python-python-daemon
import daemon

# Django stuff
sys.path.append("..")
os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"
from goove.trqacc.models import BatchServer
import updater_accounting


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


def main(args):
    global end_children
    processes = {}
    for bsname in args.batch:
        bs = BatchServer.objects.get(name=bsname)
        if bs.isactive:
            logger.info("Starting process for %s" % (bs.name))
            processes[bs] = multiprocessing.Process(target=updater_accounting.proc_func, args=(bs,))
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



def daemonize(args):
    context = daemon.DaemonContext(
            umask=0o002
            )
#    context = daemon.DaemonContext(
#            working_directory='/var/lib/goove',
#            umask=0o002,
#            pidfile=lockfile.FileLock('/var/run/goove.pid'),
#            )
#    context.signal_map = {
#            signal.SIGTERM: signal_handler
#            }
    with context:
        main(args)
    

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Start the goove updater daemon.')
    parser.add_argument("-v", "--verbose", action="store_true", help="Log information messages about what is being done.")
    parser.add_argument("-d", "--debug", action="store_true", help="Do not detach the main process and print log messages to terminal. Print debug info.")
    parser.add_argument("-b", "--batch", action="append", help="Hostname of a batch server. The updater gets its info from the database and starts feeding the data from log to the database.")
    args = parser.parse_args()

    logger = logging.getLogger("goove_updater")
    logger.setLevel(logging.WARNING)
    if args.verbose:
        logger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s[%(process)s]: %(levelname)s - %(message)s'))
    else:
        handler = logging.handlers.SysLogHandler(address="/dev/log")
        handler.setFormatter(logging.Formatter('%(name)s[%(process)s]: %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    if not args.debug:
        daemonize(args)
    else:
        main(args)

# vi:ts=4:sw=4:expandtab
