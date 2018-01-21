# -*- coding: utf-8 -*-

import os
import logging
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        help = "Create necessary upload directories"
        dirs = ['attachments', 'devices', 'logos',
                'products', 'repairs', 'return_labels',
                'settings', 'temp', 'templates']

        if not os.path.isdir(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)
        for d in dirs:
            fp = os.path.join(settings.MEDIA_ROOT, d)
            try:
                os.mkdir(fp)
            except OSError as e:
                logging.warning(e)
