from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client
from django.utils import timezone
from convention.models import TimeBlock, Registration, PaymentOption, ConInfo, BlockRegistration, get_choice
from shadowcon.tests.utils import ShadowConTestCase, data_func
from ddt import ddt
from datetime import timedelta
from reversion import revisions as reversion
import os
import json
import pytz


def get_time_blocks():
    with open(os.path.dirname(os.path.realpath(__file__)) + "/../../fixtures/initial.json") as f:
        json_data = json.load(f)

    block_data = filter(lambda x: "convention.timeblock" == x["model"], json_data)
    return map(lambda x: int(x["pk"]), block_data)


def get_payment_options():
    with open(os.path.dirname(os.path.realpath(__file__)) + "/../../fixtures/initial.json") as f:
        json_data = json.load(f)

    item_data = filter(lambda x: "convention.paymentoption" == x["model"], json_data)
    return map(lambda x: x["pk"], item_data)


class UserProfileTest(ShadowConTestCase):
    url = reverse('convention:user_profile')

    def setUp(self):
        self.client = Client()
        self.client.login(username="admin", password="123")
        self.response = self.client.get(self.url)

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + "?next=" + self.url)

    def test_javascript_accordion_hookup(self):
        self.assertSectionContains(self.response, '\\$\\(\\s?"#accordion"\\s?\\).accordion', 'head')

    def test_title(self):
        self.assertSectionContains(self.response, "ShadowCon 2016 - Account Profile", "title")

    def test_header_full_name(self):
        self.assertSectionContains(self.response, "Adrian Barnes Account Profile", "h2")

    def test_header(self):
        self.client.login(username="staff", password="123")
        self.assertSectionContains(self.client.get(self.url), "staff Account Profile", "h2")

    def test_attendance(self):
        self.assertSectionContains(self.response, "2016 Registration:\\s+<ul>\\s+<li>Friday Night: Maybe", "h2", "br /")

    def test_non_attendance(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, "2016 Registration:\\s+<ul>\\s+<li>Not Registered", "h2", "br /")

    def test_payment_option(self):
        self.assertGreater(str(self.response).find("Donation Method: Paypal"), -1)

    def test_payment_option_alternate(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        registration.payment = PaymentOption.objects.get(name="Chase Quick Pay")
        registration.save()
        response = self.client.get(self.url)
        self.assertGreater(str(response).find("Donation Method: Chase Quick Pay"), -1)

    def test_payment_option_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertEquals(str(response).find("Donation Method:"), -1)

    def test_payment_received(self):
        self.assertGreater(str(self.response).find("Donation Received: no"), -1)

    def test_payment_received_alternate(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        registration.payment_received = True
        registration.save()
        response = self.client.get(self.url)
        self.assertGreater(str(response).find("Donation Received: yes"), -1)

    def test_payment_received_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertEquals(str(response).find("Donation Received:"), -1)

    def test_registration_links_con_open(self):
        con = ConInfo.objects.all()[0]
        con.registration_opens = timezone.now() - timedelta(minutes=1)
        con.save()
        response = self.client.get(self.url)
        pattern = '<a href="%s">Change Registration</a>' % reverse('convention:register_attendance')
        self.assertGreater(str(response).find(pattern), -1)

    def test_registration_links_con_closed_no_games_submitted(self):
        con = ConInfo.objects.all()[0]
        con.registration_opens = timezone.now() + timedelta(days=1)
        con.save()
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        pattern = '<a href="%s">Change Registration</a>' % reverse('convention:register_attendance')
        self.assertEquals(str(response).find(pattern), -1)
        pattern = '<a href="%s">Change Pre-registration</a>' % reverse('convention:register_attendance')
        self.assertEquals(str(response).find(pattern), -1)

    def test_registration_links_con_closed_games_submitted(self):
        con = ConInfo.objects.all()[0]
        con.registration_opens = timezone.now() + timedelta(days=1)
        con.save()
        response = self.client.get(self.url)
        pattern = '<a href="%s">Change Pre-registration</a>' % reverse('convention:register_attendance')
        self.assertGreater(str(response).find(pattern), -1)

    def test_payment_link_not_paid(self):
        self.assertGreater(str(self.response).find('<a href="%s">Donation Options</a>' % reverse('convention:payment')),
                           -1)

    def test_payment_link_paid(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        registration.payment_received = True
        registration.save()
        response = self.client.get(self.url)
        self.assertEquals(str(response).find('<a href="%s">Donation Options</a>' % reverse('convention:payment')), -1)

    def test_payment_link_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertEquals(str(response).find('<a href="%s">Donation Options</a>' % reverse('convention:payment')), -1)

    def test_game_list(self):
        self.assertSectionContains(self.response, "Submitted Games", "h3")


@ddt
class AttendanceViewTest(ShadowConTestCase):
    url = reverse('convention:register_attendance')

    def setUp(self):
        self.client = Client()
        self.client.login(username="admin", password="123")
        self.response = self.client.get(self.url)

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + "?next=" + self.url)

    def test_header_registered(self):
        self.assertSectionContains(self.response, "Updating Registration for Adrian Barnes", "h2")

    def test_header_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Initial Registration for user", "h2")

    def test_original_reg_date_registered(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        date = registration.registration_date.astimezone(pytz.timezone('US/Pacific'))
        pattern = "Original Registration Date: %s" % date.strftime("%B %d, %Y %I:%M:%S %p %Z")
        self.assertSectionContains(self.response, pattern, "h2", 'form action="." method="POST"')

    def test_original_reg_date_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Original Registration Date", "h2", 'form action="." method="POST"', False)

    def choice_pattern(self, time_block, choice, selected):
        return '<input type="radio"\\s+id="%(id)s%(choice)s"\\s+name="%(id)s"\\s+value="%(choice)s"\\s+%(init)s\\s*' \
               '/>\\s+<label for="%(id)s%(choice)s">%(choice_value)s</label>' % \
                {"id": "block_%s" % time_block.id, "choice": choice,
                 "choice_value": get_choice(choice, BlockRegistration.ATTENDANCE_CHOICES),
                 "init": "checked" if choice == selected else ""}

    def run_initial_value_test(self, username, block_id, expected):
        self.client.login(username=username, password="123")
        response = self.client.get(self.url)

        time_block = TimeBlock.objects.get(id=block_id)
        start = 'td class="header">%s</td' % time_block.text
        for choice in BlockRegistration.ATTENDANCE_CHOICES:
            self.assertSectionContains(response, self.choice_pattern(time_block, choice[0], expected), start, "/tr")

    @data_func(get_time_blocks())
    def test_initial_values_not_registered(self, time_block_id):
        self.run_initial_value_test("user", time_block_id, BlockRegistration.ATTENDANCE_YES)

    @data_func(get_time_blocks())
    def test_initial_values_registered_with_all_maybe(self, time_block_id):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            block_reg.attendance = BlockRegistration.ATTENDANCE_MAYBE
            block_reg.save()

        self.run_initial_value_test("admin", time_block_id, BlockRegistration.ATTENDANCE_MAYBE)

    def create_block_dict(self):
        result = {}
        for block_id in get_time_blocks():
            result["block_%s" % block_id] = BlockRegistration.ATTENDANCE_MAYBE
        return result

    def test_attendance_post_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.url, self.create_block_dict())
        self.assertRedirects(response, reverse('login') + "?next=" + self.url)

    def test_attendance_post_not_registered_redirect(self):
        self.client.login(username="user", password="123")
        response = self.client.post(self.url, self.create_block_dict())
        self.assertRedirects(response, reverse('convention:payment'))

    def test_attendance_post_not_registered_model(self):
        self.client.login(username="user", password="123")
        self.client.post(self.url, self.create_block_dict())
        registration = Registration.objects.get(user=User.objects.get(username="user"))

        for block_reg in BlockRegistration.objects.filter(registration=registration):
            self.assertEquals(block_reg.attendance, BlockRegistration.ATTENDANCE_MAYBE)

    def test_attendance_post_not_registered_revision(self):
        self.client.login(username="user", password="123")
        self.client.post(self.url, self.create_block_dict())
        registration = Registration.objects.get(user=User.objects.get(username="user"))
        reg_versions = reversion.get_for_object(registration)
        self.assertEquals(len(reg_versions), 1)
        self.assertEquals(reg_versions[0].revision.comment, "Form Submission - Initial")
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            block_versions = reversion.get_for_object(block_reg)
            self.assertEquals(len(block_versions), 1)
            self.assertEquals(block_versions[0].revision, reg_versions[0].revision)

    def test_attendance_post_registered_redirect(self):
        response = self.client.post(self.url, self.create_block_dict())
        self.assertRedirects(response, reverse('convention:payment'))

    def test_attendance_post_registered_model(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            block_reg.attendance = BlockRegistration.ATTENDANCE_YES
            block_reg.save()

        self.client.post(self.url, self.create_block_dict())
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            self.assertEquals(block_reg.attendance, BlockRegistration.ATTENDANCE_MAYBE)

    def test_attendance_post_registered_revision(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            block_reg.attendance = BlockRegistration.ATTENDANCE_YES
            block_reg.save()

        self.client.post(self.url, self.create_block_dict())
        reg_versions = map(lambda x: x, reversion.get_for_object(registration))
        self.assertEquals(len(reg_versions), 1)
        self.assertEquals(reg_versions[0].revision.comment, "Form Submission - Update")

        for block_reg in BlockRegistration.objects.filter(registration=registration):
            block_versions = map(lambda x: x, reversion.get_for_object(block_reg))
            self.assertEquals(block_versions[0].revision, reg_versions[0].revision)

    def test_registration_closed(self):
        con = ConInfo.objects.all()[0]
        con.registration_opens = timezone.now() + timedelta(days=1)
        con.save()
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Registration has not opened", "h2")


@ddt
class PaymentViewTest(ShadowConTestCase):
    url = reverse('convention:payment')

    def setUp(self):
        self.client = Client()
        self.client.login(username="admin", password="123")
        self.response = self.client.get(self.url)

    def test_get_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + "?next=" + self.url)

    def test_get_on_waiting_list(self):
        con = ConInfo.objects.all()[0]
        con.max_attendees = 0
        con.save()
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Wait List Registration Recorded", "h2")

    def test_get_already_paid(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        registration.payment_received = True
        registration.save()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('convention:user_profile'))

    def test_get_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Registration Entry Not Found", "h2")

    def test_get_header(self):
        self.assertSectionContains(self.response, "Donation", "h2")

    def test_get_attendance(self):
        self.assertSectionContains(self.response, "2016 Registration:\\s+<ul>\\s+<li>Friday Night: Maybe", "h2", "br /")

    @data_func(get_payment_options())
    def test_payment_tab_headers(self, option_slug):
        option = PaymentOption.objects.get(pk=option_slug)
        pattern = '<li%s><a href="#%s" data-toggle="tab">%s</a></li>' % \
                  (' class="active"' if option.name == "Paypal" else "", option.slug, option.name)
        self.assertSectionContains(self.response, pattern, 'ul id="tabs" class="nav nav-tabs" data-tabs="tabs"', "/ul")

    @data_func(get_payment_options())
    def test_payment_tab_content(self, option_slug):
        option = PaymentOption.objects.get(pk=option_slug)
        start = 'div class="tab-pane%s" id="%s"' % (' active' if option.name == "Paypal" else "", option.slug)
        self.assertSectionContains(self.response, option.description, start, '/div')
        self.assertSectionContains(self.response, '<form action="." method="POST">', start, '/div',
                                   option.button is None)
        if option.button is not None:
            self.assertSectionContains(self.response, option.button, start, '/div')

    def test_post_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.url, {"payment": "cash"})
        self.assertRedirects(response, reverse('login') + "?next=" + self.url)

    def test_post_on_waiting_list(self):
        con = ConInfo.objects.all()[0]
        con.max_attendees = 0
        con.save()
        response = self.client.post(self.url, {"payment": "cash"})
        self.assertSectionContains(response, "Wait List Registration Recorded", "h2")
        self.assertEquals(Registration.objects.get(user=User.objects.get(username="admin")).payment.slug, 'paypal')

    def test_post_redirect(self):
        response = self.client.post(self.url, {"payment": "cash"})
        self.assertRedirects(response, reverse('convention:user_profile'))

    def test_post_model(self):
        self.client.post(self.url, {"payment": "cash"})
        self.assertEquals(Registration.objects.get(user=User.objects.get(username="admin")).payment.slug, 'cash')

    def test_post_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.post(self.url, {"payment": "cash"})
        self.assertSectionContains(response, "Registration Entry Not Found", "h2")


class AttendanceListTest(ShadowConTestCase):
    url = reverse('convention:attendance_list')

    def setUp(self):
        self.client = Client()
        self.client.login(username="admin", password="123")
        self.headers = "<tr><th></th><th>Friday Night</th><th>Friday Midnight</th><th>Saturday Morning</th><th>" \
                       "Saturday Afternoon</th><th>Saturday Evening</th><th>Saturday Midnight</th><th>Sunday Morning" \
                       "</th></tr>"
        self.payment_headers = "<tr><th></th><th>Donation Option</th><th>Donation Received</th></tr>"
        self.totals = 'table id="totals" class="attendance"'
        self.details = 'table id="details" class="attendance"'
        self.payments = 'table id="donations" class="attendance"'

        for entry in Registration.objects.all():
            entry.delete()

    def test_empty(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response, self.headers, self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>Yes</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td>"
                                             "<td>0</td><td>0</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>Maybe</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td>"
                                             "<td>0</td><td>0</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>No</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td>"
                                             "<td>0</td><td>0</td></tr>", self.totals, "/table")

        self.assertSectionContains(response, self.headers, self.details, "/table")
        self.assertEquals(1, self.get_section(response, self.details, "/table").count("<tr>"))

        self.assertSectionContains(response, self.payment_headers, self.payments, "/table")
        self.assertEquals(1, self.get_section(response, self.payments, "/table").count("<tr>"))

    def test_single_registration(self):
        new_reg = Registration(user=User.objects.filter(username="admin").get(),
                               registration_date=timezone.now(),
                               last_updated=timezone.now(),
                               payment=PaymentOption.objects.all()[0])
        new_reg.save()

        time_blocks = TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id')
        count = 0
        for block in time_blocks:
            entry = BlockRegistration(time_block=block.text, registration=new_reg,
                                      attendance=BlockRegistration.ATTENDANCE_CHOICES[count % 3][0])
            entry.save()
            count += 1

        response = self.client.get(self.url)
        self.assertSectionContains(response, "<tr><td>Yes</td><td>0</td><td>1</td><td>0</td><td>0</td><td>1</td>"
                                             "<td>0</td><td>0</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>Maybe</td><td>1</td><td>0</td><td>0</td><td>1</td><td>0</td>"
                                             "<td>0</td><td>1</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>No</td><td>0</td><td>0</td><td>1</td><td>0</td><td>0</td>"
                                             "<td>1</td><td>0</td></tr>", self.totals, "/table")
        self.assertEquals(2, self.get_section(response, self.details, "/table").count("<tr>"))
        self.assertSectionContains(response, "<tr><td>Adrian Barnes</td><td>Maybe</td><td>Yes</td><td>No</td>"
                                             "<td>Maybe</td><td>Yes</td><td>No</td><td>Maybe</td></tr>",
                                   self.details, "/table")

        self.assertEquals(2, self.get_section(response, self.payments, "/table").count("<tr>"))
        self.assertSectionContains(response, "<tr><td>Adrian Barnes</td><td>" + PaymentOption.objects.all()[0].name +
                                   "</td><td>No</td></tr>",
                                   self.payments, "/table")

    def test_double_same_registration(self):
        time_blocks = TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id')
        new_reg = Registration(user=User.objects.filter(username="admin").get(),
                               registration_date=timezone.now(),
                               last_updated=timezone.now(),
                               payment=PaymentOption.objects.all()[0])
        new_reg.save()

        count = 0
        for block in time_blocks:
            entry = BlockRegistration(time_block=block.text, registration=new_reg,
                                      attendance=BlockRegistration.ATTENDANCE_CHOICES[count % 3][0])
            entry.save()
            count += 1

        new_reg = Registration(user=User.objects.filter(username="staff").get(),
                               registration_date=timezone.now(),
                               last_updated=timezone.now(),
                               payment=PaymentOption.objects.all()[0])
        new_reg.save()

        count = 0
        for block in time_blocks:
            entry = BlockRegistration(time_block=block.text, registration=new_reg,
                                      attendance=BlockRegistration.ATTENDANCE_CHOICES[count % 3][0])
            entry.save()
            count += 1

        response = self.client.get(self.url)
        self.assertSectionContains(response, "<tr><td>Yes</td><td>0</td><td>2</td><td>0</td><td>0</td><td>2</td>"
                                             "<td>0</td><td>0</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>Maybe</td><td>2</td><td>0</td><td>0</td><td>2</td><td>0</td>"
                                             "<td>0</td><td>2</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>No</td><td>0</td><td>0</td><td>2</td><td>0</td><td>0</td>"
                                             "<td>2</td><td>0</td></tr>", self.totals, "/table")
        self.assertEquals(3, self.get_section(response, self.details, "/table").count("<tr>"))
        self.assertSectionContains(response, "<tr><td>Adrian Barnes</td><td>Maybe</td><td>Yes</td><td>No</td>"
                                             "<td>Maybe</td><td>Yes</td><td>No</td><td>Maybe</td></tr>",
                                   self.details, "/table")
        self.assertSectionContains(response, "<tr><td>staff</td><td>Maybe</td><td>Yes</td><td>No</td>"
                                             "<td>Maybe</td><td>Yes</td><td>No</td><td>Maybe</td></tr>",
                                   self.details, "/table")

        self.assertEquals(3, self.get_section(response, self.payments, "/table").count("<tr>"))
        self.assertSectionContains(response, "<tr><td>Adrian Barnes</td><td>" + PaymentOption.objects.all()[0].name +
                                   "</td><td>No</td></tr>",
                                   self.payments, "/table")
        self.assertSectionContains(response, "<tr><td>staff</td><td>" + PaymentOption.objects.all()[0].name +
                                   "</td><td>No</td></tr>",
                                   self.payments, "/table")

    def test_double_different_registration(self):
        time_blocks = TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id')
        new_reg = Registration(user=User.objects.filter(username="admin").get(),
                               registration_date=timezone.now(),
                               last_updated=timezone.now(),
                               payment=PaymentOption.objects.all()[0])
        new_reg.save()

        count = 0
        for block in time_blocks:
            entry = BlockRegistration(time_block=block.text, registration=new_reg,
                                      attendance=BlockRegistration.ATTENDANCE_CHOICES[count % 3][0])
            entry.save()
            count += 1

        new_reg = Registration(user=User.objects.filter(username="staff").get(),
                               registration_date=timezone.now(),
                               last_updated=timezone.now(),
                               payment=PaymentOption.objects.all()[1])
        new_reg.save()

        for block in time_blocks:
            entry = BlockRegistration(time_block=block.text, registration=new_reg,
                                      attendance=BlockRegistration.ATTENDANCE_CHOICES[1][0])
            entry.save()

        response = self.client.get(self.url)
        self.assertSectionContains(response, "<tr><td>Yes</td><td>1</td><td>2</td><td>1</td><td>1</td><td>2</td>"
                                             "<td>1</td><td>1</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>Maybe</td><td>1</td><td>0</td><td>0</td><td>1</td><td>0</td>"
                                             "<td>0</td><td>1</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>No</td><td>0</td><td>0</td><td>1</td><td>0</td><td>0</td>"
                                             "<td>1</td><td>0</td></tr>", self.totals, "/table")
        self.assertEquals(3, self.get_section(response, self.details, "/table").count("<tr>"))
        self.assertSectionContains(response, "<tr><td>Adrian Barnes</td><td>Maybe</td><td>Yes</td><td>No</td>"
                                             "<td>Maybe</td><td>Yes</td><td>No</td><td>Maybe</td></tr>",
                                   self.details, "/table")
        self.assertSectionContains(response, "<tr><td>staff</td><td>Yes</td><td>Yes</td><td>Yes</td>"
                                             "<td>Yes</td><td>Yes</td><td>Yes</td><td>Yes</td></tr>",
                                   self.details, "/table")

        self.assertEquals(3, self.get_section(response, self.payments, "/table").count("<tr>"))
        self.assertSectionContains(response, "<tr><td>Adrian Barnes</td><td>" + PaymentOption.objects.all()[0].name +
                                   "</td><td>No</td></tr>",
                                   self.payments, "/table")
        self.assertSectionContains(response, "<tr><td>staff</td><td>" + PaymentOption.objects.all()[1].name +
                                   "</td><td>No</td></tr>",
                                   self.payments, "/table")

    def test_single_registration_payment_received(self):
        new_reg = Registration(user=User.objects.filter(username="admin").get(),
                               registration_date=timezone.now(),
                               last_updated=timezone.now(),
                               payment=PaymentOption.objects.all()[0],
                               payment_received=True)
        new_reg.save()

        time_blocks = TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id')
        count = 0
        for block in time_blocks:
            entry = BlockRegistration(time_block=block.text, registration=new_reg,
                                      attendance=BlockRegistration.ATTENDANCE_CHOICES[count % 3][0])
            entry.save()
            count += 1

        response = self.client.get(self.url)
        self.assertEquals(2, self.get_section(response, self.payments, "/table").count("<tr>"))
        self.assertSectionContains(response, "<tr><td>Adrian Barnes</td><td>" + PaymentOption.objects.all()[0].name +
                                   "</td><td>Yes</td></tr>",
                                   self.payments, "/table")

    def test_block_added_after_registration(self):
        new_reg = Registration(user=User.objects.filter(username="admin").get(),
                               registration_date=timezone.now(),
                               last_updated=timezone.now(),
                               payment=PaymentOption.objects.all()[0])
        new_reg.save()

        time_blocks = TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id')
        count = 0
        for block in time_blocks:
            entry = BlockRegistration(time_block=block.text, registration=new_reg,
                                      attendance=BlockRegistration.ATTENDANCE_CHOICES[count % 3][0])
            entry.save()
            count += 1

        TimeBlock(text="New Block", sort_id=100).save()

        response = self.client.get(self.url)
        self.assertSectionContains(response, "<tr><td>Yes</td><td>0</td><td>1</td><td>0</td><td>0</td><td>1</td>"
                                             "<td>0</td><td>0</td><td>0</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>Maybe</td><td>1</td><td>0</td><td>0</td><td>1</td><td>0</td>"
                                             "<td>0</td><td>1</td><td>0</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>No</td><td>0</td><td>0</td><td>1</td><td>0</td><td>0</td>"
                                             "<td>1</td><td>0</td><td>0</td></tr>", self.totals, "/table")
        self.assertSectionContains(response, "<tr><td>Missing</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td>"
                                             "<td>0</td><td>0</td><td>1</td></tr>", self.totals, "/table")
        self.assertEquals(2, self.get_section(response, self.details, "/table").count("<tr>"))
        self.assertSectionContains(response, "<tr><td>Adrian Barnes</td><td>Maybe</td><td>Yes</td><td>No</td>"
                                             "<td>Maybe</td><td>Yes</td><td>No</td><td>Maybe</td><td>Missing</td></tr>",
                                   self.details, "/table")
