# -*- coding: utf-8 -*-

from django.views.generic.base import RedirectView
from django.conf.urls import url

from servo.views import checkin


urlpatterns = [
    url(r'^$', checkin.index, name='checkin-index'),
    url(r'^sn/$', RedirectView.as_view(url='/checkin/', permanent=True)),
    url(r'^customer/$', checkin.get_customer, name='checkin-get_customer'),
    url(r'^reset/$', checkin.reset, name='checkin-reset'),
    url(r'^status/$', checkin.status, name='checkin-status'),
    url(r'^checkin/print/(\w+)/$', checkin.print_confirmation, name='checkin-print'),
    url(r'^thanks/(\w+)/$', checkin.thanks, name='checkin-thanks'),
    url(r'^terms/$', checkin.terms, name='checkin-terms'),
]
