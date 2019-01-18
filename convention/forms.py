from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import CharField, ChoiceField, Form
from django.utils import timezone
from django.utils.translation import ugettext as _
from registration.forms import RegistrationForm as BaseRegistrationForm, get_user_model
from reversion import revisions as reversion

from .models import BlockRegistration, TimeBlock, Registration, PaymentOption, Referral
from .utils import get_registration, friendly_username, get_current_con
from contact.utils import mail_list

from collections import OrderedDict
import pytz


# Test code for NewUserForm is in shadowcon/tests/test_registration
class NewUserForm(BaseRegistrationForm):
    first_name = CharField(max_length=30, required=False)
    last_name = CharField(max_length=30, required=False)
    referral_code = CharField(max_length=8, required=False)

    class Meta(BaseRegistrationForm.Meta):
        fields = [
            get_user_model().USERNAME_FIELD,
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        ]

    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')

        if code == "":
            return code

        referrals = Referral.objects.filter(code=code)
        if len(referrals) is 0:
            raise ValidationError(_("The provided referral code %s does not exist." % code), code="invalid referral")

        referral = referrals[0]
        if referral.referred_user is not None:
            raise ValidationError(_("The provided referral code %s has already been used." % code), code="already used referral")

        return code


class AttendanceForm(Form):
    def __init__(self, user=None, *args, **kwargs):
        super(AttendanceForm, self).__init__(*args, **kwargs)

        convention = get_current_con()
        registration = Registration.objects.filter(user=user).filter(convention=convention)
        if registration:
            self.registration = registration[0]
            date = self.registration.registration_date.astimezone(pytz.timezone('US/Pacific'))
            self.registration_str = date.strftime("%B %d, %Y %I:%M:%S %p %Z")
        self.user = user
        self.user_friendly = friendly_username(user)

        if 'data' not in kwargs:
            kwargs['data'] = {}
            if registration:
                entries = BlockRegistration.objects.filter(registration=self.registration)
                for entry in entries:
                    time_block = TimeBlock.objects.filter(text__exact=entry.time_block)
                    if time_block:
                        kwargs['data']["block_%s" % time_block[0].id] = entry.attendance

        for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
            initial = kwargs['data'].get("block_%s" % time_block.id, BlockRegistration.ATTENDANCE_YES)
            self.fields["block_%s" % time_block.id] = ChoiceField(choices=BlockRegistration.ATTENDANCE_CHOICES,
                                                                  label=time_block.text,
                                                                  initial=initial)

    def time_block_fields(self):
        return OrderedDict((k, v) for k, v in self.fields.iteritems() if k.startswith("block_"))

    def send_mail(self, registration, new_entry):
        subject_details = "%s Registration for %s" % ("Initial" if new_entry else "Updated", self.user_friendly)
        message = self.user_friendly + " will be attending for:\n"
        for entry in get_registration(self.user):
            message += " - %s\n" % entry

        date = registration.registration_date.astimezone(pytz.timezone('US/Pacific'))
        message += "\nInitially registered on %s" % date.strftime("%B %d, %Y %I:%M:%S %p %Z")

        mail_list("Registration", subject_details, message, list_name="registration")

    def save(self):
        new_entry = not hasattr(self, "registration")
        if new_entry:
            self.registration = Registration(convention=get_current_con(),
                                             user=self.user,
                                             registration_date=timezone.now(),
                                             payment=PaymentOption.objects.all()[0])

        with transaction.atomic(), reversion.create_revision():
            reversion.set_user(self.user)
            reversion.set_comment("Form Submission - %s" % ("Initial" if new_entry else "Update"))

            self.registration.last_updated = timezone.now()
            self.registration.save()

            old_regs = {}
            for reg in BlockRegistration.objects.filter(registration=self.registration):
                old_regs[reg.time_block] = reg

            for key, field in self.time_block_fields().iteritems():
                time_block = TimeBlock.objects.filter(id=key.split("_")[1])[0].text
                if time_block in old_regs:
                    old_regs[time_block].attendance = field.initial
                    old_regs[time_block].save()
                    del old_regs[time_block]
                else:
                    BlockRegistration(registration=self.registration, time_block=time_block,
                                      attendance=field.initial).save()

            for obsolete in old_regs.values():
                obsolete.delete()

        self.send_mail(self.registration, new_entry)

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
