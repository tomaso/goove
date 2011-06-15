from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'goove.trqlive.mainviews.homepage'),

    (r'^static/$', 'goove.trqlive.mainviews.homepage_static'),

    (r'^dynamic/nodes_overview/$', 'goove.trqlive.dynamicviews.nodes_overview'),
    (r'^dynamic/nodes_overview/(?P<subcluster_name>.*)/$', 'goove.trqlive.dynamicviews.nodes_overview'),
    (r'^dynamic/subclusters_list/$', 'goove.trqlive.dynamicviews.subclusters_list'),
    (r'^dynamic/subclusters_list/(?P<batchserver_name>.*)/$', 'goove.trqlive.dynamicviews.subclusters_list'),
    (r'^dynamic/batchservers_list/$', 'goove.trqlive.dynamicviews.batchservers_list'),

    (r'^api/', include('goove.trqlive.api.urls')),

    (r'^nodes/$', 'goove.trqlive.nodeviews.node_overview'),


#    (r'^/(?P<servername>.*)/nodes/detail/(?P<nodename>.*)/$', 'goove.trqlive.nodeviews.node_detail'),
#    (r'^nodes/detail/(?P<nodename>.*)/$', 'goove.trqacc.nodeviews.node_detail'),
#    (r'^nodes/detail/$', 'goove.trqacc.nodeviews.node_detail'),
#    (r'^nodes/listing/(?P<filtertype>.*)/(?P<filtervalue>.*)/$', 'goove.trqacc.nodeviews.nodes_listing'),
#    (r'^nodes/listing/$', 'goove.trqacc.nodeviews.nodes_listing'),
#    (r'^nodes/table/$', 'goove.trqacc.nodeviews.nodes_table'),
#    (r'^nodes/table/with_detail/(?P<nodename>.*)/$', 'goove.trqacc.nodeviews.nodes_table'),
#    (r'^nodes/table/json_detail/$', 'goove.trqacc.nodeviews.nodes_table_json_detail'),
#
#    (r'^queues/graph/$', 'goove.trqacc.queueviews.graph'),
#    (r'^queues/stats/$', 'goove.trqacc.queueviews.queues_stats'),
#    (r'^queues/detail/(?P<servername>.*)/(?P<queuename>.*)/$', 'goove.trqacc.queueviews.queue_detail'),
#    (r'^queues/detail/$', 'goove.trqacc.queueviews.queue_detail'),
#    (r'^queues/table/$', 'goove.trqacc.queueviews.queues_overview'),
#
#    (r'^users/user_detail/(?P<servername>.*)/(?P<username>.*)/$', 'goove.trqacc.userviews.user_detail'),
#    (r'^users/user_detail/$', 'goove.trqacc.userviews.user_detail'),
#    (r'^users/group_detail/(?P<groupname>.*)/$', 'goove.trqacc.userviews.group_detail'),
#    (r'^users/group_detail/$', 'goove.trqacc.userviews.group_detail'),
#    (r'^users/griduser_detail/(?P<gridusername>.*)/$', 'goove.trqacc.userviews.griduser_detail'),
#    (r'^users/griduser_detail/$', 'goove.trqacc.userviews.griduser_detail'),
#
#    (r'^jobs/suspicious/$', 'goove.trqacc.jobviews.suspicious'),
#    (r'^jobs/stats/$', 'goove.trqacc.jobviews.stats'),
#    (r'^jobs/detail/(?P<servername>.*)/(?P<jobid>.*)/$', 'goove.trqacc.jobviews.job_detail'),
#    (r'^jobs/detail/$', 'goove.trqacc.jobviews.job_detail'),
#    (r'^jobs/completed_listing/$', 'goove.trqacc.jobviews.jobs_completed_listing'),
#    (r'^jobs/running/$', 'goove.trqacc.jobviews.jobs_running'),
#    (r'^jobs/report_form/$', 'goove.trqacc.jobviews.report_form'),
#    (r'^jobs/report_output/$', 'goove.trqacc.jobviews.report_output'),
#    (r'^jobs/fairshare/$', 'goove.trqacc.jobviews.fairshare'),
#
#    (r'^jobs/graph/$', 'goove.trqacc.jobviews.graph'),
#
#    (r'^$', 'goove.trqacc.generalviews.overview'), 


#    (r'^nodes/$', 'django.views.generic.list_detail.object_list', dict(queryset=nodes, paginate_by=10)),
)
