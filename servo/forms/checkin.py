# -*- coding: utf-8 -*-

import gsxws

from django import forms
from datetime import date
from django.conf import settings
from django_countries import countries
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _
from django.forms.extras.widgets import SelectDateWidget

from servo.validators import (apple_sn_validator,
                              phone_validator,
                              file_upload_validator,)

from servo.forms.base import SearchFieldInput
from servo.models import (Configuration, Device,
                          Attachment, Location,
                          Customer,)


# Generate list of years for purchase date picker
y = date.today().year
YEARS = [x + 1 for x in xrange(y - 10, y)]


def get_checkin_locations(user):
    """Return possible checkin location choices for this user."""
    from servo.models import User
    if user.is_authenticated():
        return user.locations.enabled()
    else:
        user_id = Configuration.conf('checkin_user')
        return User.objects.get(pk=user_id).locations.enabled()


class ConfirmationForm(forms.Form):
    confirm = forms.BooleanField(required=False)


class DeviceForm(forms.ModelForm):

    required_css_class = 'required'

    purchase_country = forms.ChoiceField(
        label=_('Country'),
        choices=countries,
        initial=settings.INSTALL_COUNTRY
    )
    accessories = forms.CharField(
        required=False,
        label=_('Accessories'),
        widget=forms.Textarea(attrs={'class': 'span12', 'rows': 3}),
        help_text=_("Please list here any accessories you'd like to check in with your device (cables, power adapters, bags, etc)")
    )

    pop = forms.FileField(
        required=False,
        label=_('Proof of Purchase'),
        validators=[file_upload_validator],
        help_text=_('Proof of Purchase is required when setting purchase date manually')
    )

    condition = forms.CharField(
        label=_('Condition of device'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'span12', 'rows': 3}),
        help_text=_("Please describe the condition of the device")
    )

    class Meta:
        model = Device
        fields = (
            'description',
            'sn',
            'imei',
            'purchased_on',
            'purchase_country',
            'username',
            'password',
        )
        widgets = {
            'sn': SearchFieldInput(),
            'password': forms.PasswordInput(),
            'username': forms.TextInput(),
            'purchased_on': SelectDateWidget(years=YEARS),
            'warranty_status': forms.Select(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):

        super(DeviceForm, self).__init__(*args, **kwargs)

        if Configuration.false('checkin_require_password'):
            self.fields['password'].required = False

        if Configuration.true('checkin_require_condition'):
            self.fields['condition'].required = True

        if kwargs.get('instance'):
            prod = gsxws.Product('')
            prod.description = self.instance.description

            if prod.is_ios:
                self.fields['password'].label = _('Passcode')

            if not prod.is_ios:
                del(self.fields['imei'])
            if not prod.is_mac:
                del(self.fields['username'])

        if Configuration.true('checkin_password'):
            self.fields['password'].widget = forms.TextInput(attrs={'class': 'span12'})


class CustomerForm(forms.Form):

    from django.utils.safestring import mark_safe

    required_css_class = 'required'

    fname = forms.CharField(label=_('First name'))
    lname = forms.CharField(label=_('Last name'))

    company = forms.CharField(
        required=False,
        label=_('Company (optional)')
    )
    email = forms.EmailField(
        label=_('Email address'),
        widget=forms.TextInput(attrs={'class': 'span12'})
    )
    phone = forms.CharField(
        label=_('Phone number'),
        validators=[phone_validator]
    )
    address = forms.CharField(label=_('Address'))
    country = forms.ChoiceField(
        label=_('Country'),
        choices=Customer.COUNTRY_CHOICES,
        initial=settings.INSTALL_COUNTRY
    )
    city = forms.CharField(label=_('City'))
    postal_code = forms.CharField(label=_('Postal Code'))
    checkin_location = forms.ModelChoiceField(
        empty_label=None,
        label=_(u'Check-in location'),
        queryset=Location.objects.enabled(),
        widget=forms.Select(attrs={'class': 'span12'}),
        help_text=_('Choose where you want to leave the device')
    )
    checkout_location = forms.ModelChoiceField(
        empty_label=None,
        label=_(u'Check-out location'),
        queryset=Location.objects.enabled(),
        widget=forms.Select(attrs={'class': 'span12'}),
        help_text=_('Choose where you want to pick up the device')
    )
    TERMS = _('I agree to the <a href="/checkin/terms/" target="_blank">terms of service.</a>')
    agree_to_terms = forms.BooleanField(initial=False, label=mark_safe(TERMS))

    notify_by_sms = forms.BooleanField(
        initial=True,
        required=False,
        label=_('Notify by SMS')
    )
    notify_by_email = forms.BooleanField(
        initial=True,
        required=False,
        label=_('Notify by Email')
    )

    def clean_fname(self):
        v = self.cleaned_data.get('fname')
        return v.capitalize()

    def clean_lname(self):
        lname = self.cleaned_data.get('lname')
        return lname.capitalize()

    def __init__(self, request, *args, **kwargs):

        super(CustomerForm, self).__init__(*args, **kwargs)

        location = request.session['checkin_location']
        locations = get_checkin_locations(request.user)

        self.fields['checkin_location'].queryset = locations
        self.fields['checkin_location'].initial = location
        self.fields['checkout_location'].queryset = locations
        self.fields['checkout_location'].initial = location

        if request.user.is_authenticated():
            del(self.fields['agree_to_terms'])
            self.fields['phone'].widget = SearchFieldInput()


class AppleSerialNumberForm(forms.Form):
    sn = forms.CharField(
        min_length=8,
        validators=[apple_sn_validator],
        label=_(u'Serial number or IMEI')
    )

    def clean_sn(self):
        sn = self.cleaned_data.get('sn')
        return sn.upper()


class SerialNumberForm(forms.Form):
    sn = forms.CharField(
        min_length=8,
        label=_(u'Serial number')
    )

    def clean_sn(self):
        sn = self.cleaned_data.get('sn')
        return sn.upper()


class StatusCheckForm(forms.Form):
    code = forms.CharField(
        min_length=8,
        label=_('Service Order'),
        validators=[RegexValidator(regex=r'\d{8}', message=_('Invalid Service Order number'))]
    )


class IssueForm(forms.Form):

    required_css_class = 'required'

    issue_description = forms.CharField(
        min_length=10,
        #initial='Does not work very well',
        label=_(u'Problem description'),
        widget=forms.Textarea(attrs={'class': 'span12'})
    )
    attachment = forms.FileField(
        required=False,
        label=_(u'Attachment'),
        validators=[file_upload_validator],
        help_text=_(u'Please use this to attach relevant documents')
    )

    notes = forms.CharField(
        required=False,
        label=_(u'Notes'),
        widget=forms.Textarea(attrs={'class': 'span12'}),
        help_text=_(u'Will not appear on the print-out')
    )


class QuestionForm(forms.Form):
    question = forms.CharField(widget=forms.HiddenInput)
    answer = forms.CharField(widget=forms.HiddenInput)


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        exclude = []
