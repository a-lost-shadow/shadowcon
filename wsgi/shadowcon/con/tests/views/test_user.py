from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client
from django.utils import timezone
from con.models import TimeBlock, Registration, PaymentOption, ConInfo, BlockRegistration, get_choice
from shadowcon.tests.utils import ShadowConTestCase, data_func
from ddt import ddt
from datetime import timedelta
import os
import json
import pytz


def get_time_blocks():
    with open(os.path.dirname(os.path.realpath(__file__)) + "/../../fixtures/initial.json") as f:
        json_data = json.load(f)

    block_data = filter(lambda x: "con.timeblock" == x["model"], json_data)
    return map(lambda x: int(x["pk"]), block_data)


def get_payment_options():
    with open(os.path.dirname(os.path.realpath(__file__)) + "/../../fixtures/initial.json") as f:
        json_data = json.load(f)

    item_data = filter(lambda x: "con.paymentoption" == x["model"], json_data)
    return map(lambda x: x["pk"], item_data)


class UserProfileTest(ShadowConTestCase):
    url = reverse('con:user_profile')

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
        self.assertGreater(str(self.response).find("Payment Method: Paypal"), -1)

    def test_payment_option_alternate(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        registration.payment = PaymentOption.objects.get(name="Chase Quick Pay")
        registration.save()
        response = self.client.get(self.url)
        self.assertGreater(str(response).find("Payment Method: Chase Quick Pay"), -1)

    def test_payment_option_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertEquals(str(response).find("Payment Method:"), -1)

    def test_payment_received(self):
        self.assertGreater(str(self.response).find("Payment Received: no"), -1)

    def test_payment_received_alternate(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        registration.payment_received = True
        registration.save()
        response = self.client.get(self.url)
        self.assertGreater(str(response).find("Payment Received: yes"), -1)

    def test_payment_received_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertEquals(str(response).find("Payment Received:"), -1)

    def test_registration_links_open(self):
        con = ConInfo.objects.all()[0]
        con.registration_opens = timezone.now() - timedelta(minutes=1)
        con.save()
        response = self.client.get(self.url)
        pattern = '<a href="%s">Change Registration</a>' % reverse('con:register_attendance')
        self.assertGreater(str(response).find(pattern), -1)

    def test_registration_links_closed(self):
        con = ConInfo.objects.all()[0]
        con.registration_opens = timezone.now() + timedelta(days=1)
        con.save()
        response = self.client.get(self.url)
        pattern = '<a href="%s">Change Registration</a>' % reverse('con:register_attendance')
        self.assertEquals(str(response).find(pattern), -1)

    def test_payment_link_not_paid(self):
        self.assertGreater(str(self.response).find('<a href="%s">Payment Options</a>' % reverse('con:payment')), -1)

    def test_payment_link_paid(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        registration.payment_received = True
        registration.save()
        response = self.client.get(self.url)
        self.assertEquals(str(response).find('<a href="%s">Payment Options</a>' % reverse('con:payment')), -1)

    def test_payment_link_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertEquals(str(response).find('<a href="%s">Payment Options</a>' % reverse('con:payment')), -1)

    def test_game_list(self):
        self.assertSectionContains(self.response, "Submitted Games", "h3")


@ddt
class AttendanceViewTest(ShadowConTestCase):
    url = reverse('con:register_attendance')

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
        self.assertRedirects(response, reverse('con:payment'))

    def test_attendance_post_not_registered_model(self):
        self.client.login(username="user", password="123")
        self.client.post(self.url, self.create_block_dict())
        registration = Registration.objects.get(user=User.objects.get(username="user"))
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            self.assertEquals(block_reg.attendance, BlockRegistration.ATTENDANCE_MAYBE)

    def test_attendance_post_registered_redirect(self):
        response = self.client.post(self.url, self.create_block_dict())
        self.assertRedirects(response, reverse('con:payment'))

    def test_attendance_post_registered_model(self):
        registration = Registration.objects.get(user=User.objects.get(username="admin"))
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            block_reg.attendance = BlockRegistration.ATTENDANCE_YES
            block_reg.save()

        self.client.post(self.url, self.create_block_dict())
        for block_reg in BlockRegistration.objects.filter(registration=registration):
            self.assertEquals(block_reg.attendance, BlockRegistration.ATTENDANCE_MAYBE)

    def test_registration_closed(self):
        con = ConInfo.objects.all()[0]
        con.registration_opens = timezone.now() + timedelta(days=1)
        con.save()
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Registration has not opened", "h2")


@ddt
class PaymentViewTest(ShadowConTestCase):
    url = reverse('con:payment')

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
        self.assertRedirects(response, reverse('con:user_profile'))

    def test_get_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Registration Entry Not Found", "h2")

    def test_get_header(self):
        self.assertSectionContains(self.response, "Payment", "h2")

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
        self.assertRedirects(response, reverse('con:user_profile'))

    def test_post_model(self):
        self.client.post(self.url, {"payment": "cash"})
        self.assertEquals(Registration.objects.get(user=User.objects.get(username="admin")).payment.slug, 'cash')

    def test_post_not_registered(self):
        self.client.login(username="user", password="123")
        response = self.client.post(self.url, {"payment": "cash"})
        self.assertSectionContains(response, "Registration Entry Not Found", "h2")

