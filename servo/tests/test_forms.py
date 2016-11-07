# -*- coding: utf-8 -*-

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware

from servo.models.common import Configuration
from servo.forms.checkin import CustomerForm

from servo.tests.test_views import add_middleware_to_request


class CheckinTestCase(TestCase):
    def test_customer(self):
        factory = RequestFactory()
        request = factory.get('/checkin/')
        request.user = AnonymousUser
        request = add_middleware_to_request(request, SessionMiddleware)
        #form = CustomerForm(request)
