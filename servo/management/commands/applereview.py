# -*- coding: utf-8 -*-

import logging
import pyexcel as pe
from time import time
from django.core.management.base import BaseCommand

from servo.models import Order


class Command(BaseCommand):

    help = "Export data for Apple Review"

    def add_arguments(self, parser):
        parser.add_argument('year', type=int, help='Start year for report')
        parser.add_argument('rfp_msg', help='Ready for pickup message')
        parser.add_argument('status_id', help='ID of "completed" status')
        parser.add_argument('outfile', help='Path to results file')

    def handle(self, *args, **options):
        data = []
        start_time = time()
        ts_fmt = '%Y-%m-%d'
        header = [
            'SERVICE_ORDER', 'DATE_CREATED', 'DATE_COMPLETED',
            'DATE_CFP',
            'CUSTOMER_NAME', 'CUSTOMER_ADDRESS', 'CUSTOMER_PHONE',
            'UNIT_SERIAL_NUMBER', 'REPORTED_SYMPTOMS', 'TECH_SYMPTOMS',
            'UNIT_WTY_STATUS', 'REPAIR_COST', 'PARTS_REPLACED',
            'GSX_REPAIRS',
        ]

        data.append(header)
        orders = Order.objects.filter(created_at__year__gte=options['year'])

        for o in orders.exclude(customer=None).order_by('created_at'):
            cust_name = o.get_customer_name() or ''
            cust_name = cust_name.encode('utf-8')
            cust_addr = o.customer.street_address
            cust_phone = o.customer.phone
            device = o.get_devices().first()

            if device:
                device_sn = device.sn
                device_wty = device.get_warranty_status_display()
            else:
                device_sn = '-'
                device_wty = '-'

            notes = o.notes().filter(is_reported=True)
            if notes:
                customer_notes = notes[0].body
                tech_notes = [x.body + ' - ' + x.created_by.full_name for x in notes[1:]]
            else:
                customer_notes = ''
                tech_notes = ''

            parts = [x.code for x in o.get_parts()]
            repairs = [x.confirmation for x in o.get_repairs()]
            created_at = o.created_at.strftime(ts_fmt)

            status_closed = o.orderstatus_set.filter(status_id=options['status_id']).first()
            closed_at = status_closed.started_at.strftime(ts_fmt) if status_closed else '-'
            rfp_message = o.notes().filter(body__contains=options['rfp_msg']).first()

            if rfp_message:
                custom_cfp = rfp_message.created_at.strftime(ts_fmt)
            else:
                custom_cfp = '-'

            row = [o.code, created_at, closed_at, custom_cfp,
                   cust_name, cust_addr, cust_phone,
                   device_sn, customer_notes, ';'.join(tech_notes),
                   device_wty,
                   str(o.net_total()),
                   ', '.join(parts),
                   ', '.join(repairs)]

            data.append(row)

        sheet = pe.Sheet(data)
        sheet.save_as(options['outfile'], encoding='UTF-8')
        seconds = int(time() - start_time)
        logging.info('%d records exported in %d seconds' % (len(data) - 1), seconds)
