from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^nodes/$', 'goove.trq.views.nodes_overview'),
#    (r'^nodes/$', 'django.views.generic.list_detail.object_list', dict(queryset=nodes, paginate_by=10)),
)
