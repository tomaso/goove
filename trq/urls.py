from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^nodes/detail/(?P<nodename>.*)/$', 'goove.trq.nodeviews.node_detail'),
    (r'^nodes/detail/$', 'goove.trq.nodeviews.node_detail'),
    (r'^nodes/listing/(?P<filtertype>.*)/(?P<filtervalue>.*)/$', 'goove.trq.nodeviews.nodes_listing'),
    (r'^nodes/listing/$', 'goove.trq.nodeviews.nodes_listing'),
    (r'^nodes/table/$', 'goove.trq.nodeviews.nodes_table'),

    (r'^queues/graph/$', 'goove.trq.queueviews.graph'),
    (r'^queues/stats/$', 'goove.trq.queueviews.queues_stats'),
    (r'^queues/detail/(?P<queuename>.*)/$', 'goove.trq.queueviews.queue_detail'),
    (r'^queues/detail/$', 'goove.trq.queueviews.queue_detail'),
    (r'^queues/table/$', 'goove.trq.queueviews.queues_overview'),

    (r'^users/(?P<username>.*)/$', 'goove.trq.userviews.user_detail'),
    (r'^users/$', 'goove.trq.userviews.users_overview'),

    (r'^jobs/suspicious/$', 'goove.trq.jobviews.suspicious'),
    (r'^jobs/stats/$', 'goove.trq.jobviews.stats'),
    (r'^jobs/detail/(?P<servername>.*)/(?P<jobid>.*)/$', 'goove.trq.jobviews.job_detail'),
    (r'^jobs/detail/$', 'goove.trq.jobviews.job_detail'),
    (r'^jobs/completed_listing/$', 'goove.trq.jobviews.jobs_completed_listing'),

    (r'^jobs/graph/$', 'goove.trq.jobviews.graph'),

    (r'^$', 'goove.trq.generalviews.overview'), 


#    (r'^nodes/$', 'django.views.generic.list_detail.object_list', dict(queryset=nodes, paginate_by=10)),
)
