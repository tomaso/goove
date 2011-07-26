from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',

    (r'^nodes_overview/$', 'goove.trqacc.dynamicviews.nodes_overview'),                                                                                                                                     
    (r'^nodes_overview/(?P<batchserver_name>.*)/(?P<subcluster_name>.*)/$', 'goove.trqacc.dynamicviews.nodes_overview'),                                                                                                             
    (r'^nodes_list/(?P<batchserver_name>.*)/$', 'goove.trqacc.dynamicviews.nodes_list'),                                                                                                                    
                                                                                                                                                                                                                     
                                                                                                                                                                                                                     
    (r'^subclusters_list/$', 'goove.trqacc.dynamicviews.subclusters_list'),                                                                                                                                 
    (r'^subclusters_list/(?P<batchserver_name>.*)/$', 'goove.trqacc.dynamicviews.subclusters_list'),                                                                                                        
    (r'^batchservers_list/$', 'goove.trqacc.dynamicviews.batchservers_list'),                                                                                                                               
                                                                                                                                                                                                                     
    (r'^queues_list/(?P<batchserver_name>.*)/$', 'goove.trqacc.dynamicviews.queues_list'),                                                                                                                  
                                                                                                                                                                                                                     
    (r'^jobs_list/(?P<batchserver_name>.*)/$', 'goove.trqacc.dynamicviews.jobs_list'),     

)

# vi:ts=4:sw=4:expandtab
