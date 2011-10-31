from trqacc.models import JobSlot, Node, NodeProperty, NodeState, SubCluster, GridUser, User, Group, JobState, Queue, SubmitHost, EventAttribute

JobStateCache = {}
JobSlotCache = {}
QueueCache = {}
NodeCache = {}
UserCache = {}
GroupCache = {}
SubmitHostCache = {}
EventAttributeCache = {}

#
# Caching functions, we do not have one for Jobs as there are too many of them
#
def getJobState(state):
    """
    Get JobState db object (from cache or database). Valid states are: Q,R,C,L
    """
    global JobStateCache
    if not JobStateCache.has_key(state):
        JobStateCache[state] =  JobState.objects.get(shortname=state)
    return JobStateCache[state]


def getJobSlot(slot,node):
    """
    Get JobSlot db object (from cache or database).
    """
    global JobSlotCache
    created = False
    if not JobSlotCache.has_key((slot,node)):
        JobSlotCache[(slot,node)],created = JobSlot.objects.get_or_create(slot=slot,node=node)
    return (JobSlotCache[(slot,node)],created)


def getQueue(qname,ts):
    """
    Return tuple (queue object, created)
    """
    global QueueCache
    created = False
    if not QueueCache.has_key((qname,ts)):
        QueueCache[(qname,ts)],created = Queue.objects.get_or_create(name=qname,server=ts)
    return (QueueCache[(qname,ts)],created)


def getNode(nname, ts):
    global NodeCache
    created = False
    if not NodeCache.has_key((nname,ts)):
        NodeCache[(nname,ts)],created = Node.objects.get_or_create(name=nname,server=ts)
    return (NodeCache[(nname,ts)],created)


def getUser(uname, ts, group=None):
    global UserCache
    created = False
    if not UserCache.has_key(uname):
        UserCache[uname],created = User.objects.get_or_create(name=uname, server=ts, group=group)
    return (UserCache[uname],created)


def getGroup(gname,ts):
    global GroupCache
    created = False
    if not GroupCache.has_key(gname):
        GroupCache[gname],created = Group.objects.get_or_create(name=gname,server=ts)
    return (GroupCache[gname],created)


def getSubmitHost(shname):
    global SubmitHostCache
    created = False
    if not SubmitHostCache.has_key(shname):
        SubmitHostCache[shname],created = SubmitHost.objects.get_or_create(name=shname)
    return (SubmitHostCache[shname],created)


def getEventAttribute(eaname):
    global EventAttributeCache
    created = False
    if not EventAttributeCache.has_key(eaname):
        EventAttributeCache[eaname],created = EventAttribute.objects.get_or_create(name=eaname)
    return (EventAttributeCache[eaname],created)

# vi:ts=4:sw=4:expandtab
