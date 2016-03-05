from django.forms import CharField, ChoiceField, Form
from registration.forms import RegistrationForm as BaseRegistrationForm, get_user_model

from .models import BlockRegistration, TimeBlock
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

        if 'data' not in kwargs:
            kwargs['data'] = {}
            if registration:
                entries = BlockRegistration.objects.filter(registration=registration)
                for entry in entries:
                    kwargs['data']["block_%s" % entry.time_block.id] = entry.attendance

        for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
            initial = kwargs['data'].get("block_%s" % time_block.id, BlockRegistration.ATTENDANCE_YES)
            self.fields["block_%s" % time_block.id] = ChoiceField(choices=BlockRegistration.ATTENDANCE_CHOICES,
                                                                  label=time_block.text,
                                                                  initial=initial)
        self.fields["Test"] = CharField(max_length=30, required=False)

    def time_block_fields(self):
        return OrderedDict((k, v) for k, v in self.fields.iteritems() if k.startswith("block_"))

    def save(self, registration):
        for key, field in self.time_block_fields().iteritems():
            time_block = TimeBlock.objects.filter(id=key.split("_")[1])[0]
            BlockRegistration(registration=registration, time_block=time_block, attendance=field.initial).save()
