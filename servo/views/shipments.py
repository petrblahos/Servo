# -*- coding: utf-8 -*-

import gsxws
from decimal import *

from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.forms.models import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404

from servo.lib.utils import paginate
from servo.models import GsxAccount, ServicePart, Shipment, PurchaseOrderItem
from servo.forms.product import PurchaseOrderItemForm, IncomingSearchForm
from servo.forms.returns import *


def prep_counts():
    incoming = PurchaseOrderItem.objects.filter(received_at=None)
    incoming = incoming.exclude(purchase_order__submitted_at=None).count()

    returns = Shipment.objects.exclude(dispatched_at=None).count()
    return locals()


def prep_list_view(request):
    """
    Prepares the list view for incoming parts and products
    """
    from datetime import timedelta
    now = timezone.now()

    data = {'can_receive': True}
    data['counts'] = prep_counts()
    location = request.user.get_location()

    ordered_date_range  = [now - timedelta(days=30), timezone.now()]
    received_date_range = [now - timedelta(days=30), timezone.now()]

    initial = {
        'location': location,
        'ordered_start_date': ordered_date_range[0],
        'ordered_end_date': ordered_date_range[1],
    }

    if request.method == 'POST':
        data['form'] = IncomingSearchForm(request.POST, initial=initial)
    else:
        data['form'] = IncomingSearchForm(initial=initial)

    inventory = PurchaseOrderItem.objects.filter(received_at=None).select_related('purchase_order', 'sales_order')
    inventory = inventory.exclude(purchase_order__submitted_at=None)

    if request.method == 'POST':
        fdata = request.POST

        loc = fdata.get('location')
        if loc:
            inventory = PurchaseOrderItem.objects.filter(purchase_order__location=loc)

        ordered_sd = fdata.get('ordered_start_date')
        if ordered_sd:
            ordered_date_range[0] = ordered_sd
            inventory = inventory.filter(purchase_order__submitted_at__range=ordered_date_range)

        received_sd = fdata.get('received_start_date')
        if received_sd:
            received_date_range[0] = received_sd
            inventory = inventory.filter(received_at__range=received_date_range)

        conf = fdata.get('confirmation')
        if conf:
            inventory = PurchaseOrderItem.objects.filter(purchase_order__confirmation=conf)

        service_order = fdata.get('service_order')
        if service_order:
            inventory = PurchaseOrderItem.objects.filter(purchase_order__sales_order__code=service_order)

    page = request.GET.get("page")
    inventory = inventory.order_by('-id')
    data['count'] = inventory.count()
    data['inventory'] = paginate(inventory, page, 200)
    data['title'] = _(u"%d incoming products") % data['count']

    return data


def list_incoming(request, shipment=None, status=""):
    """
    Lists purchase order items that have not arrived yet
    """
    data = prep_list_view(request)

    if request.POST.getlist("id"):
        count = len(request.POST.getlist("id"))
        for i in request.POST.getlist("id"):
            item = PurchaseOrderItem.objects.get(pk=i)
            try:
                item.receive(request.user)
            except ValueError as e:
                messages.error(request, e)
                return redirect(list_incoming)

        messages.success(request, _("%d products received") % count)

        return redirect(list_incoming)

    return render(request, "shipments/list_incoming.html", data)


def view_incoming(request, pk):
    """
    Shows an incoming part
    """
    next = False
    item = get_object_or_404(PurchaseOrderItem, pk=pk)

    data = prep_list_view(request)

    data['next'] = ""
    data['subtitle'] = item.code

    try:
        next = item.get_next_by_created_at(received_at=None)
        data['next'] = next.pk
    except PurchaseOrderItem.DoesNotExist:
        pass  # That was the last of them...

    if request.method == "POST":

        item.received_by = request.user
        item.received_at = timezone.now()

        form = PurchaseOrderItemForm(request.POST, instance=item)

        if form.is_valid():
            try:
                item = form.save()
            except gsxws.GsxError as e:
                messages.error(request, e)
                return redirect(view_incoming, date, pk)

            messages.success(request, _(u"Product %s received") % item.code)

            if next:
                return redirect(view_incoming, next.pk)
            else:
                return redirect(list_incoming)
    else:
        form = PurchaseOrderItemForm(instance=item)

    data['form'] = form
    data['item'] = item
    data['url'] = request.path

    return render(request, "products/receive_item.html", data)


def list_returns(request, shipment=None, date=None):
    return render(request, "shipments/list_returns.html", locals())


def return_label(request, code, return_order):

    GsxAccount.default(request.user)

    try:
        label = gsxws.Returns(return_order)
        return HttpResponse(label.returnLabelFileData, content_type="application/pdf")
    except Exception as e:
        messages.add_message(request, messages.ERROR, e)
        return redirect('products-list')


def list_bulk_returns(request):
    from django.db.models import Count
    title = _("Browse Bulk Returns")
    returns = Shipment.objects.exclude(dispatched_at=None).annotate(num_parts=Count('servicepart'))

    page = request.GET.get("page")
    returns = paginate(returns, page, 50)
    counts = prep_counts()

    return render(request, "shipments/list_bulk_returns.html", locals())


def view_packing_list(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    pdf = shipment.packing_list.read()
    return HttpResponse(pdf, content_type="application/pdf")


def view_bulk_return(request, pk):
    title = _("View bulk return")
    shipment = get_object_or_404(Shipment, pk=pk)
    return render(request, "shipments/view_bulk_return.html", locals())


def edit_bulk_return(request, pk=None, ship_to=None):
    """
    Edits the bulk return shipment before it's submitted
    """
    location = request.user.get_location()
    accounts = location.get_shipto_choices()

    if len(accounts) < 1:
        messages.error(request, _(u'Location %s has no Ship-To') % location.title)
        return redirect('products-list_products')

    if not ship_to:
        ship_to = accounts[0][0]
        return redirect(edit_bulk_return, ship_to=ship_to)

    shipment = Shipment.get_current(request.user, location, ship_to)
    part_count = shipment.servicepart_set.all().count()
    PartFormSet = inlineformset_factory(Shipment,
                                        ServicePart,
                                        form=BulkReturnPartForm,
                                        extra=0,
                                        exclude=[])
    
    form = BulkReturnForm(instance=shipment)
    formset = PartFormSet(instance=shipment)
    
    if request.method == "POST":
        form = BulkReturnForm(request.POST, instance=shipment)
        if form.is_valid():
            formset = PartFormSet(request.POST, instance=shipment)
            if formset.is_valid():
                shipment = form.save()
                msg = _("Bulk return saved")
                formset.save()
                
                if "confirm" in request.POST.keys():
                    try:
                        shipment.register_bulk_return(request.user)
                        msg = _(u"Bulk return %s submitted") % shipment.return_id
                        messages.success(request, msg)
                        return redirect(view_bulk_return, shipment.pk)
                    except Exception as e:
                        messages.error(request, e)
                        return redirect(edit_bulk_return, ship_to=ship_to)
                messages.success(request, msg)
                return redirect(edit_bulk_return, ship_to=ship_to)
            else:
                messages.error(request, formset.errors)
        else:
            messages.error(request, form.errors)

    counts = prep_counts()
    counts['pending_return'] = len(formset)
    title = _(u"%d parts pending return") % part_count
    return render(request, "shipments/edit_bulk_return.html", locals())


def remove_from_return(request, pk, part_pk):
    """
    Removes a part from a bulk return
    """
    shipment = get_object_or_404(Shipment, pk=pk)
    part = get_object_or_404(ServicePart, pk=part_pk)

    try:
        shipment.toggle_part(part)
        messages.success(request, _(u"Part %s removed from bulk return") % part.part_number)
    except Exception as e:
        messages.error(request, e)

    return redirect(edit_bulk_return)


def add_to_return(request, pk, part=None):
    """
    Adds a part to a bulk return
    """
    data = {'action': request.path}

    if pk and part:
        shipment = get_object_or_404(Shipment, pk=pk)
        part = get_object_or_404(ServicePart, pk=part)
        shipment.servicepart_set.add(part)
        messages.success(request, _(u"Part %s added to return") % part.part_number)

        return redirect(edit_bulk_return)

    if request.method == "POST":
        query = request.POST.get('q')
        results = ServicePart.objects.filter(return_order=query)
        data = {'shipment': pk, 'results': results}

        return render(request, "shipments/add_to_return-results.html", data)

    return render(request, "shipments/add_to_return.html", data)


def update_part(request, part, return_type):
    """
    Update part status to GSX
    """
    part = get_object_or_404(ServicePart, pk=part)
    return_type = int(return_type)
    
    msg     = ""
    form    = ""
    title   = ""

    if return_type == Shipment.RETURN_DOA:
        title = _("Return DOA Part")
        form = DoaPartReturnForm(part=part)

    if return_type == Shipment.RETURN_GPR:
        title = _("Return Good Part")
        form = GoodPartReturnForm()

    if return_type == Shipment.RETURN_CTS:
        title = _("Convert to Stock")
        msg = _("This part will be converted to regular inventory")
        form = ConvertToStockForm(initial={'partNumber': part.part_number})

    if request.method == "POST":

        if return_type == Shipment.RETURN_DOA:
            form = DoaPartReturnForm(part=part, data=request.POST)
        if return_type == Shipment.RETURN_GPR:
            form = GoodPartReturnForm(request.POST)
        if return_type == Shipment.RETURN_CTS:
            form = ConvertToStockForm(request.POST)

        if form.is_valid():
            try:
                part.update_part(form.cleaned_data, return_type, request.user)
                messages.success(request, _("Part updated"))
            except Exception as e:
                messages.error(request, e)
        else:
            messages.error(request, form.errors)

        return redirect(part.order_item.order)

    action = request.path
    return render(request, "shipments/update_part.html", locals())


def parts_pending_return(request, ship_to):
    """
    Returns the part pending return for this GSX Account
    """
    pass


def verify(request, pk):
    shipment = Shipment.objects.get(pk=pk)
    return redirect(shipment)
