from django.conf.urls import url

from . import views

app_name = 'page'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^page/(?P<url>[A-Za-z0-9_/]+)/$', views.display, name='display'),
]
