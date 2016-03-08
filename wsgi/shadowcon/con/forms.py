from django.core.exceptions import ValidationError
from django.forms import CharField, ChoiceField, Form
from django.utils.translation import ugettext as _
from registration.forms import RegistrationForm as BaseRegistrationForm, get_user_model

from .models import BlockRegistration, TimeBlock
from .utils import get_registration, friendly_username
from contact.utils import mail_list

from collections import OrderedDict
import pytz


class NewUserForm(BaseRegistrationForm):
    first_name = CharField(max_length=30, required=False)
    last_name = CharField(max_length=30, required=False)

    class Meta(BaseRegistrationForm.Meta):
        fields = [
            get_user_model().USERNAME_FIELD,
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        ]


class AttendanceForm(Form):
    def __init__(self, registration=None, user=None, *args, **kwargs):
        super(AttendanceForm, self).__init__(*args, **kwargs)

        if registration:
            date = registration[0].registration_date.astimezone(pytz.timezone('US/Pacific'))
            self.registration = date.strftime("%B %d, %Y %I:%M:%S %p %Z")
        self.user = user
        self.user_friendly = friendly_username(user)

        if 'data' not in kwargs:
            kwargs['data'] = {}
            if registration:
                entries = BlockRegistration.objects.filter(registration=registration)
                for entry in entries:
                    time_block = TimeBlock.objects.filter(text__exact=entry.time_block)
                    if time_block:
                        kwargs['data']["block_%s" % time_block[0].id] = entry.attendance

        for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
            initial = kwargs['data'].get("block_%s" % time_block.id, BlockRegistration.ATTENDANCE_YES)
            self.fields["block_%s" % time_block.id] = ChoiceField(choices=BlockRegistration.ATTENDANCE_CHOICES,
                                                                  label=time_block.text,
                                                                  initial=initial)
        self.fields["Test"] = CharField(max_length=30, required=False)

    def time_block_fields(self):
        return OrderedDict((k, v) for k, v in self.fields.iteritems() if k.startswith("block_"))

    def send_mail(self, registration, new_entry):
        subject_details = "%s for %s" % ("Initial Registration" if new_entry else "Updated Registration",
                                         self.user_friendly)
        message = self.user_friendly + " will be attending for:\n"
        for entry in get_registration(self.user):
            message += " - %s\n" % entry

        date = registration.registration_date.astimezone(pytz.timezone('US/Pacific'))
        message += "\nInitial registered on %s" % date.strftime("%B %d, %Y %I:%M:%S %p %Z")

        mail_list("Registration", subject_details, message, "no-reply@shadowcon.net", list_name="registration")

    def save(self, registration, new_entry):
        for key, field in self.time_block_fields().iteritems():
            time_block = TimeBlock.objects.filter(id=key.split("_")[1])[0].text
            BlockRegistration(registration=registration, time_block=time_block, attendance=field.initial).save()

        self.send_mail(registration, new_entry)

    def clean(self):
        result = super(AttendanceForm, self).clean()
        found_attendance = False
        for key, value in result.iteritems():
            if key.startswith("block_") and value != BlockRegistration.ATTENDANCE_NO:
                found_attendance = True
                break
        if not found_attendance:
            raise ValidationError(_("You must register attendance at one or more sessions.  If you wish to  " +
                                    "unregister, please use the contact us at the bottom of the page."),
                                  code="invalid data")
        return result
