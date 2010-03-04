from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^nodes/detail/(?P<nodename>.*)/$', 'goove.trq.nodeviews.node_detail'),
    (r'^nodes/table_list/$', 'goove.trq.nodeviews.nodes_table_list'),
    (r'^nodes/$', 'goove.trq.nodeviews.nodes_overview'),

    (r'^queues/graph/$', 'goove.trq.queueviews.graph'),
    (r'^queues/stats/$', 'goove.trq.queueviews.queues_stats'),
    (r'^queues/(?P<queuename>.*)/$', 'goove.trq.queueviews.queue_detail'),
    (r'^queues/$', 'goove.trq.queueviews.queues_overview'),

    (r'^users/(?P<username>.*)/$', 'goove.trq.userviews.user_detail'),
    (r'^users/$', 'goove.trq.userviews.users_overview'),

    (r'^jobs/stats/$', 'goove.trq.jobviews.stats'),
    (r'^jobs/page/(?P<page>\d+)$', 'goove.trq.jobviews.jobs_overview'),
    (r'^jobs/(?P<servername>.*)/(?P<jobid>.*)/$', 'goove.trq.jobviews.job_detail'),
    (r'^jobs/$', 'goove.trq.jobviews.jobs_overview'),

    (r'^jobs/graph/$', 'goove.trq.jobviews.graph'),

    (r'^$', 'goove.trq.generalviews.overview'), 


#    (r'^nodes/$', 'django.views.generic.list_detail.object_list', dict(queryset=nodes, paginate_by=10)),
)
