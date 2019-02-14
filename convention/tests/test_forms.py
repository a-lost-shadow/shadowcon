from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from ..forms import AttendanceForm
from ..models import Registration, BlockRegistration, TimeBlock, PaymentOption, ConInfo
from ..utils import friendly_username
from datetime import timedelta
from django.utils import timezone
from shadowcon.tests.utils import ShadowConTestCase, data_func
from ddt import ddt
import pytz
import json
import os


def get_user_registration(user_id):
    with open(os.path.dirname(os.path.realpath(__file__)) + "/../fixtures/initial.json") as f:
        data = json.load(f)

    reg_data = filter(lambda x: "convention.registration" == x["model"] and user_id == x["fields"]["user"], data)
    result = []
    if len(reg_data) > 0:
        reg_id = reg_data[0]["pk"]
        blocks = filter(lambda x: "convention.blockregistration" == x["model"] and
                                  reg_id == x["fields"]["registration"],
                        data)
        result = map(lambda x: x["pk"], blocks)

    return result


def set_registration(registration, time_block, attendance):
    reg = BlockRegistration(time_block=time_block, registration=registration, attendance=attendance)
    reg.save()
    return reg


@ddt
class FormsTest(ShadowConTestCase):
    # Test code for NewUserForm is in shadowcon/tests/test_registration

    def run_attendance_order_test(self, user):
        TimeBlock(text="Before Everything", sort_id=0).save()

        form = AttendanceForm(user=user)

        time_blocks = TimeBlock.objects.all().order_by('sort_id')
        index = -1
        for k, v in form.fields.iteritems():
            if k.startswith("block_"):
                index += 1
                self.assertEquals(v.label, time_blocks[index].text)

    def test_attendance_form_no_registration_field_order(self):
        user = User(username="username")
        user.save()
        self.assertEquals(0, len(Registration.objects.filter(user=user)))
        self.run_attendance_order_test(user)

    def test_attendance_form_with_registration_field_order(self):
        user = User.objects.get(id=1)
        self.assertEquals(1, len(Registration.objects.filter(user=user)))
        self.run_attendance_order_test(user)

    def test_attendance_form_no_registration_initial(self):
        user = User(username="username")
        user.save()
        self.assertEquals(0, len(Registration.objects.filter(user=user)))

        form = AttendanceForm(user=user)
        time_blocks = TimeBlock.objects.all()
        for time_block in time_blocks:
            self.assertEquals(BlockRegistration.ATTENDANCE_YES, form.fields["block_%d" % time_block.id].initial)

    def test_attendance_form_registration_string_not_registered(self):
        user = User(username="username")
        user.save()
        form = AttendanceForm(user=user)
        self.assertFalse(hasattr(form, "registration_str"))

    def test_attendance_form_registration_string_registered(self):
        user = User.objects.get(username="admin")
        form = AttendanceForm(user=user)

        registration = Registration.objects.get(user=user)
        date = registration.registration_date.astimezone(pytz.timezone('US/Pacific'))

        self.assertEquals(form.registration_str, date.strftime("%B %d, %Y %I:%M:%S %p %Z"))

    @data_func(get_user_registration(1))
    def test_attendance_form_with_registration_initial(self, block_id):
        block_reg = BlockRegistration.objects.get(id=block_id)

        user = User.objects.get(id=1)
        form = AttendanceForm(user=user)
        time_block = TimeBlock.objects.get(text=block_reg.time_block)
        self.assertEquals(form.fields["block_%d" % time_block.id].initial, block_reg.attendance)

    def test_attendance_form_time_block_function_order(self):
        TimeBlock(text="Before Everything", sort_id=0).save()

        form = AttendanceForm(user=User(username="username"))

        time_blocks = TimeBlock.objects.all().order_by('sort_id')
        index = -1
        for k, v in form.time_block_fields().iteritems():
            index += 1
            self.assertEquals(v.label, time_blocks[index].text)

    def check_attendance_email(self, initial, registration, expected_message):
        username = friendly_username(registration.user)

        if initial:
            subject = 'ShadowCon [Registration]: Initial Registration for %s' % username
        else:
            subject = 'ShadowCon [Registration]: Updated Registration for %s' % username

        date = registration.registration_date.astimezone(pytz.timezone('US/Pacific'))
        expected_message += "\nInitially registered on %s" % date.strftime("%B %d, %Y %I:%M:%S %p %Z")

        self.assertEmail(['admin-test@mg.shadowcon.net'], expected_message, subject=subject)

    def test_attendance_form_save_email_initial(self):
        user = User(username="username")
        user.save()

        form = AttendanceForm(user=user)

        form.save()

        expected_message = "username will be attending for:\n"
        for time_block in TimeBlock.objects.all().order_by('sort_id'):
            expected_message += " - %s: Yes\n" % time_block.text

        self.check_attendance_email(True, Registration.objects.get(user=user), expected_message)

    def test_attendance_form_save_email_update(self):
        user = User(username="username", first_name="First", last_name="Last")
        user.save()

        registration = Registration(user=user, registration_date=timezone.now()-timedelta(days=1),
                                    last_updated=timezone.now(), payment=PaymentOption.objects.all()[0],
                                    payment_received=True, convention=ConInfo.objects.all()[0])
        registration.save()

        set_registration(registration, "Friday Night", BlockRegistration.ATTENDANCE_MAYBE)
        set_registration(registration, "Friday Midnight", BlockRegistration.ATTENDANCE_MAYBE)
        set_registration(registration, "Sunday Morning", BlockRegistration.ATTENDANCE_NO)

        form = AttendanceForm(user=user)

        for block_reg in BlockRegistration.objects.filter(registration=registration):
            block_reg.delete()

        form.save()

        expected_message = """First Last will be attending for:
 - Friday Night: Maybe
 - Friday Midnight: Maybe
 - Saturday Morning: Yes
 - Saturday Afternoon: Yes
 - Saturday Evening: Yes
 - Saturday Midnight: Yes
"""

        self.check_attendance_email(False, registration, expected_message)

    def test_attendance_form_save_model_initial(self):
        user = User(username="username")
        user.save()

        form = AttendanceForm(user=user)

        self.assertEquals(len(Registration.objects.filter(user=user)), 0)

        form.save()

        self.assertEquals(len(Registration.objects.filter(user=user)), 1)
        registration = Registration.objects.get(user=user)

        self.assertEquals(len(BlockRegistration.objects.filter(registration=registration)), 7)
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            self.assertEquals(block_reg.attendance, BlockRegistration.ATTENDANCE_YES)

    def test_attendance_form_save_model_update(self):
        user = User(username="username")
        user.save()

        first_registered = timezone.now() - timedelta(days=1)
        registration = Registration(user=user, registration_date=first_registered, last_updated=first_registered,
                                    payment=PaymentOption.objects.all()[0], payment_received=True, convention=ConInfo.objects.all()[0])
        registration.save()
        form = AttendanceForm(user=user)

        init_sat_night = set_registration(registration, "Saturday Evening", BlockRegistration.ATTENDANCE_NO)
        init_sat_mid = set_registration(registration, "Saturday Midnight", BlockRegistration.ATTENDANCE_NO)
        init_bad = set_registration(registration, "Sunday DNE", BlockRegistration.ATTENDANCE_NO)

        self.assertEquals(len(BlockRegistration.objects.filter(registration=registration)), 3)

        modified_date = timezone.now()
        for k in form.time_block_fields().keys():
            form.fields[k].initial = BlockRegistration.ATTENDANCE_MAYBE
        form.save()

        updated_registration = Registration.objects.get(id=registration.id)
        self.assertEquals(updated_registration.registration_date, first_registered)
        self.assertGreater(updated_registration.last_updated, modified_date)

        self.assertEquals(len(BlockRegistration.objects.filter(registration=registration)), 7)
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            self.assertEquals(block_reg.attendance, BlockRegistration.ATTENDANCE_MAYBE)

        self.assertEquals(BlockRegistration.objects.get(id=init_sat_night.id).attendance,
                          BlockRegistration.ATTENDANCE_MAYBE)
        self.assertEquals(BlockRegistration.objects.get(id=init_sat_mid.id).attendance,
                          BlockRegistration.ATTENDANCE_MAYBE)
        self.assertEquals(len(BlockRegistration.objects.filter(id=init_bad.id)), 0)

    def test_unregister_fail(self):
        user = User(username="username")
        user.save()

        form = AttendanceForm(user=user)
        form.cleaned_data = {}
        for k in form.time_block_fields().keys():
            form.cleaned_data[k] = BlockRegistration.ATTENDANCE_NO

        with self.assertRaises(ValidationError) as e:
            form.clean()
        self.assertEquals(e.exception.message,
                          "You must register attendance at one or more sessions.  If you wish to  " +
                          "unregister, please use the contact us at the bottom of the page.")

    def test_clean_passes_with_one_attendance_entry(self):
        user = User(username="username")
        user.save()

        form = AttendanceForm(user=user)
        form.cleaned_data = {}
        last = None
        for k in form.time_block_fields().keys():
            form.cleaned_data[k] = BlockRegistration.ATTENDANCE_NO
            last = k
        form.cleaned_data[last] = BlockRegistration.ATTENDANCE_YES

        form.clean()
