from django.forms import CharField, ChoiceField, Form
from registration.forms import RegistrationForm as BaseRegistrationForm, get_user_model

from .models import Registration, BlockRegistration, TimeBlock
from collections import OrderedDict


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


class AttendenceForm(Form):
    def __init__(self, *args, **kwargs):
        super(AttendenceForm, self).__init__(*args, **kwargs)

        for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
            if 'data' in kwargs:
                initial = kwargs['data'].get(time_block.text, BlockRegistration.ATTENDANCE_YES)
            else:
                initial = BlockRegistration.ATTENDANCE_YES
            self.fields["block_%s" % time_block.id] = ChoiceField(choices=BlockRegistration.ATTENDANCE_CHOICES,
                                                                  label=time_block.text,
                                                                  initial=initial)
        self.fields["Test"] = CharField(max_length=30, required=False)

    def time_block_fields(self):
        return OrderedDict((k, v) for k, v in self.fields.iteritems() if k.startswith("block_"))
