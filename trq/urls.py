from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^nodes/(?P<nodename>.*)/$', 'goove.trq.nodeviews.node_detail'),
    (r'^nodes/$', 'goove.trq.nodeviews.nodes_overview'),

    (r'^queues/(?P<queuename>.*)/$', 'goove.trq.queueviews.queue_detail'),
    (r'^queues/$', 'goove.trq.queueviews.queues_overview'),

    (r'^users/(?P<username>.*)/$', 'goove.trq.userviews.user_detail'),
    (r'^users/$', 'goove.trq.userviews.users_overview'),

#    (r'^nodes/$', 'django.views.generic.list_detail.object_list', dict(queryset=nodes, paginate_by=10)),
)
