from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('',

    # common pages
    (r'^$', direct_to_template, {'template': 'main.html'}),

    (r'^config/personal/$', 'goove.trqacc.configviews.personal'),



    # data for ext js (mainly json returning "pages")

    (r'^dynamic.html$', direct_to_template, {'template': 'dynamic.html'}),

    (r'^api/', include('goove.trqacc.api.urls')),

    # static pages - really rendering templates

    (r'^static/', include('goove.trqacc.static.urls')),
)

# vi:ts=4:sw=4:expandtab
