from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Only for development. TODO: remove
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '%s/site_media/' % settings.ROOT_PATH}),
    # (r'^goove/', include('goove.foo.urls')),
    (r'^trqacc/', include('goove.trqacc.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

)
