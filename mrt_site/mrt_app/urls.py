from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('mrt_app.views',
    (r'^index$', 'index'),
    (r'^$', 'results_redirect'),
    (r'^(?P<from_artist>[^/]+)/to/(?P<to_artist>[^/]+)/(?P<track_count>[\d]+)-tracks/$', 'results'),
    (r'^(?P<from_artist>[^/]+)/to/(?P<to_artist>[^/]+)/$', 'results'),
    (r'^suggestions/(?P<prefix>[^/]+).json$', 'suggestions_json'),
    (r'^(?P<from_artist>[^/]+)/to/(?P<to_artist>[^/]+)/ready.json$', 'ready_json'),
    (r'^(?P<from_artist>[^/]+)/to/(?P<to_artist>[^/]+)/[\d]+-tracks/ready.json$', 'ready_json')

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
