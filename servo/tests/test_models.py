# -*- coding: utf-8 -*-

import unittest
from django.test import TestCase

from servo.models.common import Configuration
from servo.models.order import Order
from servo.models.account import User
from servo.models.queue import Queue


class ConfigurationTests(TestCase):
    def test_checkin_user(self):
        uid = Configuration.conf('checkin_user')
        u = User.objects.get(pk=uid)
        self.assertEquals(u.pk, int(uid))


class ServiceOrderTests(TestCase):
    def test_checkin(self):
        uid = Configuration.conf('checkin_user')
        u = User.objects.get(pk=uid)
        o = Order(created_by=u)
        o.save()
        o.check_in(u)
        self.assertEquals(o.location, o.checkin_location)


class QueueTests(TestCase):
    def test_absolute_url(self):
        q = Queue.objects.get(pk=1)
        self.assertRegexpMatches(q.get_absolute_url(), r'\?queue=\d$')


if __name__ == '__main__':
    unittest.main()
