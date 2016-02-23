from django.conf.urls import url

from . import views

app_name = 'contact'
urlpatterns = [
    url(r'^$', views.ContactView.as_view(), name='contact'),
    url(r'^thanks/$', views.ThanksView.as_view(), name='thanks'),
]
