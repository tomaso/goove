import os
import sys
sys.path.append("..")

os.environ['DJANGO_SETTINGS_MODULE']="goove.settings"

from django.db import connection
from django.db.models.sql.aggregates import Aggregate
from django.db.models import Max
from trq.models import Job

class MyMax(Aggregate):
    sql_function = 'MAX'
    #sql_template = '%(function)s(%(field)s) test'
    """A base class to make it easy for end users to define their own
    custom SQL aggregates.

    The subclass should define the following two class properties:
     * sql_function - the name of the SQL function to invoke

    Optionally, you can define
      * sql_template - a format string that is used to compose the
        SQL that will be sent to the database. The template will be
        provided with the following substitution variables:
          - ``function``, the sql fuction that will be invoked
          - ``field``, the resolved name of the column to be
            operated on.
        The template will also be provided with any keyword argument
        provided to the aggregate when it was defined.
        The default template is '%(function)s(%(field)s)'
      * is_ordinal - a boolean, True if the result of the aggregate
        will always be a count, regardless of the field on which the
        aggregate is applied. False by default.
      * is_computed - a boolean, True if the result of the aggregate
        will always be a float, regardless of the field on which the
        aggregate is applied. False by default.
    """
    def __init__(self, lookup, **extra):
        self.lookup = lookup
        self.extra = extra
	# this is not perfect but I don't know how to do it right :(
    	self.sql_template = '%(function)s(unix_timestamp(%(field)s) - unix_timestamp(' + extra['sub'] + '))'
        print str(extra)

    def _default_alias(self):
        return '%s__%s' % (self.lookup, self.__class__.__name__.lower())
    default_alias = property(_default_alias)

    def add_to_query(self, query, alias, col, source, is_summary):
        super(MyMax, self).__init__(col, source, is_summary, **self.extra)
        query.aggregate_select[alias] = self 


#try:
#    Job.objects.filter(jobid=10).aggregate(MyMax("walltime","prdel"))
#except:
#    pass
Job.objects.filter(jobid=10).aggregate(Max("walltime"),MyMax("comp_time",sub="start_time"))


print connection.queries[-1]

