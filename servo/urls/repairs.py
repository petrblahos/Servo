# -*- coding: utf-8 -*-

from django.conf.urls import url

from servo.views import gsx


urlpatterns = [
    url(r'^(\d+)/delete/$', gsx.delete_repair, name="repairs-delete_repair"),
    url(r'^(\d+)/parts/(\d+)/remove/$', gsx.remove_part, name="repairs-remove_part"),
    url(r'^(\d+)/parts/(\d+)/add/$', gsx.add_part, name="repairs-add_part"),
    url(r'^(\d+)/parts/(\d+)/update_sn/$', gsx.update_sn, name="repairs-update_sn"),
    url(r'^(\d+)/copy/$', gsx.copy_repair, name="repairs-copy_repair"),
    url(r'^(\d+)/check_parts/$', gsx.check_parts_warranty, name="repairs-check_parts"),
]
