# -*- coding: utf-8 -*-

import subprocess
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        help = "Delete pg backups older than 3 months"
        subprocess.call(['find', settings.BACKUP_DIR,
                         '-ctime', '+12w', '-type', 'f',
                         '-name', '*.pgdump', '-delete'])
