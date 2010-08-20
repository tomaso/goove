from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^nodes/detail/(?P<nodename>.*)/$', 'goove.trq.nodeviews.node_detail'),
    (r'^nodes/detail/$', 'goove.trq.nodeviews.node_detail'),
    (r'^nodes/listing/(?P<filtertype>.*)/(?P<filtervalue>.*)/$', 'goove.trq.nodeviews.nodes_listing'),
    (r'^nodes/listing/$', 'goove.trq.nodeviews.nodes_listing'),
    (r'^nodes/table/$', 'goove.trq.nodeviews.nodes_table'),
    (r'^nodes/table/with_detail/(?P<nodename>.*)/$', 'goove.trq.nodeviews.nodes_table'),
    (r'^nodes/table/json_detail/$', 'goove.trq.nodeviews.nodes_table_json_detail'),

    (r'^queues/graph/$', 'goove.trq.queueviews.graph'),
    (r'^queues/stats/$', 'goove.trq.queueviews.queues_stats'),
    (r'^queues/detail/(?P<servername>.*)/(?P<queuename>.*)/$', 'goove.trq.queueviews.queue_detail'),
    (r'^queues/detail/$', 'goove.trq.queueviews.queue_detail'),
    (r'^queues/table/$', 'goove.trq.queueviews.queues_overview'),

    (r'^users/user_detail/(?P<username>.*)/$', 'goove.trq.userviews.user_detail'),
    (r'^users/user_detail/$', 'goove.trq.userviews.user_detail'),
    (r'^users/group_detail/(?P<groupname>.*)/$', 'goove.trq.userviews.group_detail'),
    (r'^users/group_detail/$', 'goove.trq.userviews.group_detail'),
    (r'^users/griduser_detail/(?P<gridusername>.*)/$', 'goove.trq.userviews.griduser_detail'),
    (r'^users/griduser_detail/$', 'goove.trq.userviews.griduser_detail'),

    (r'^jobs/suspicious/$', 'goove.trq.jobviews.suspicious'),
    (r'^jobs/stats/$', 'goove.trq.jobviews.stats'),
    (r'^jobs/detail/(?P<servername>.*)/(?P<jobid>.*)/$', 'goove.trq.jobviews.job_detail'),
    (r'^jobs/detail/$', 'goove.trq.jobviews.job_detail'),
    (r'^jobs/completed_listing/$', 'goove.trq.jobviews.jobs_completed_listing'),
    (r'^jobs/report_form/$', 'goove.trq.jobviews.report_form'),
    (r'^jobs/report_output/$', 'goove.trq.jobviews.report_output'),
    (r'^jobs/fairshare/$', 'goove.trq.jobviews.fairshare'),

    (r'^jobs/graph/$', 'goove.trq.jobviews.graph'),

    (r'^$', 'goove.trq.generalviews.overview'), 


#    (r'^nodes/$', 'django.views.generic.list_detail.object_list', dict(queryset=nodes, paginate_by=10)),
)
