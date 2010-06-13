from django import forms
from models import Job
import subprocess
from xml.dom.minidom import parse, parseString
from xml.parsers.expat import ExpatError
import signal

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

class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise Alarm

def UpdateRunningJob(job):
    """
    Update data of a running job from torque server
    Currently only xml output of `qstat -x` is supported
    """
    signal.signal(signal.SIGALARM, alarm_handler)
    signal.alarm(20)
    try:
        proc = subprocess.Popen(["qstat", "-x", "%s.%s" % (job., job.server.name)], stdout=subprocess.PIPE)
        stdoutdata, stderrdata = proc.communicate()
        signal.alarm(0)  # reset the alarm
    except Alarm:
        print "Oops, taking too long!"

# vi:sw=4:ts=4:et
