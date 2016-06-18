from ddt import ddt, data
from django.core.urlresolvers import reverse
from django.test import Client
from reversion_compare.admin import CompareVersionAdmin
from shadowcon.tests.utils import ShadowConTestCase
from unittest import TestCase

from .admin import EmailListAdmin, ContactReasonAdmin
from .models import EmailList
from .utils import mail_list


class ContactTest(ShadowConTestCase):
    url = reverse("contact:contact")
    field_required = '<ul class="errorlist"><li>This field is required.</li></ul>'

    def setUp(self):
        self.client = Client()
        self.test_data = {"name": "test name",
                          "email": "test@test.com",
                          "reason": "1",
                          "summary": "test summary",
                          "message": "test message",
                          }

    def test_get_form(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, "ShadowCon 2016 - Contact Us", "title")

    def test_get_thanks(self):
        response = self.client.get(reverse('contact:thanks'))
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, "<h2>Thank you for contacting us", "h2")

    def run_missing_test(self, key):
        del self.test_data[key]
        response = self.client.post(self.url, self.test_data)
        self.assertSectionContains(response, self.field_required, 'label for="id_%s"' % key, '/tr')
        self.assertEquals(1, str(response).count(self.field_required))

    def test_missing_name(self):
        self.run_missing_test('name')

    def test_missing_email(self):
        self.run_missing_test('email')

    def test_missing_reason(self):
        self.run_missing_test('reason')

    def test_missing_summary(self):
        self.run_missing_test('summary')

    def test_missing_message(self):
        self.run_missing_test('message')

    def test_missing_all(self):
        response = self.client.post(self.url, {})
        self.assertEquals(5, str(response).count(self.field_required))

    def test_invalid_reason(self):
        self.test_data['reason'] = "This isn't valid"
        expected_error = '<ul class="errorlist"><li>Select a valid choice. That choice is not ' \
                         'one of the available choices.</li></ul>'
        response = self.client.post(self.url, self.test_data)
        self.assertSectionContains(response, expected_error, 'label for="id_reason"', '/tr')
        self.assertEquals(1, str(response).count(expected_error))

    def test_success_redirect(self):
        response = self.client.post(self.url, self.test_data)
        self.assertRedirects(response, reverse("contact:thanks"))

    def check_reply(self, email, name, address):
        self.assertEquals(email.reply_to, [self.from_address, "%s <%s>" % (name, address)])

    def test_success_email(self):
        self.client.post(self.url, self.test_data)

        email = self.get_email()

        self.assertEquals(email.body, "E-mail from '%s <%s>':\n%s" % (
            self.test_data['name'],
            self.test_data['email'],
            self.test_data['message']))
        self.assertEquals(email.to, ['staff@na.com', 'admin@na.com'])
        self.assertEquals(email.from_email, self.from_address)
        self.check_reply(email, self.test_data['name'], self.test_data['email'])
        self.assertEquals(email.subject, 'ShadowCon [Something Broke]: %s' % self.test_data['summary'])

    def run_unclean_test(self, key):
        new_data = self.test_data.copy()
        new_data[key] = "<a>%s</a>" % self.test_data[key]

        self.client.post(self.url, new_data)

        email = self.get_email()

        self.assertEquals(email.body, "E-mail from '%s <%s>':\n%s" % (
            self.test_data['name'],
            self.test_data['email'],
            self.test_data['message']))
        self.assertEquals(email.to, ['staff@na.com', 'admin@na.com'])
        self.assertEquals(email.from_email, self.from_address)
        self.check_reply(email, self.test_data['name'], self.test_data['email'])
        self.assertEquals(email.subject, 'ShadowCon [Something Broke]: %s' % self.test_data['summary'])

    def test_cleaned_name(self):
        self.run_unclean_test('name')

    def test_cleaned_email(self):
        self.test_data['email'] = "<a>%s</a>" % self.test_data['email']
        expected_error = '<ul class="errorlist"><li>Enter a valid email address.</li></ul>'
        response = self.client.post(self.url, self.test_data)
        self.assertSectionContains(response, expected_error, 'label for="id_email"', '/tr')
        self.assertEquals(1, str(response).count(expected_error))

    def test_cleaned_summary(self):
        self.run_unclean_test('summary')

    def test_cleaned_message(self):
        self.run_unclean_test('message')

    def test_success_email_alternate(self):
        test_data = {"name": "Different Name",
                     "email": "na@na.net",
                     "reason": "2",
                     "summary": "A summary goes here",
                     "message": "My precious",
                     }
        self.client.post(self.url, test_data)

        email = self.get_email()

        self.assertEquals(email.body, "E-mail from '%s <%s>':\n%s" % (
            test_data['name'],
            test_data['email'],
            test_data['message']))
        self.assertEquals(email.to, ['user@na.com'])
        self.assertEquals(email.from_email, self.from_address)
        self.check_reply(email, test_data['name'], test_data['email'])
        self.assertEquals(email.subject, 'ShadowCon [Admins make things better]: A summary goes here')


@ddt
class AdminVersionTest(TestCase):
    @data(EmailListAdmin, ContactReasonAdmin)
    def test_has_versions(self, clazz):
        self.assertTrue(CompareVersionAdmin.__subclasscheck__(clazz))


class UtilsTest(ShadowConTestCase):
    def run_base_test(self, reply_to):
        subject_source = "Itch"
        subject_details = "In my brain"
        message = "I can't scratch it"
        mail_list(subject_source, subject_details, message, EmailList.objects.get(name="Admin"), reply_to=reply_to)

        email = self.get_email()

        self.assertEquals(email.body, message)
        self.assertEquals(email.to, ['user@na.com'])
        self.assertEquals(email.from_email, self.from_address)
        self.assertEquals(email.subject, 'ShadowCon [%s]: %s' % (subject_source, subject_details))

        return email

    def test_util(self):
        email = self.run_base_test(reply_to=None)
        self.assertEquals(email.reply_to, [])

    def test_util_alternate(self):
        subject_source = "World Domination"
        subject_details = "Is at hand"
        message = "Now only $5.95"
        mail_list(subject_source, subject_details, message, list_name="Website")

        email = self.get_email()

        self.assertEquals(email.body, message)
        self.assertEquals(email.to, ['staff@na.com', 'admin@na.com'])
        self.assertEquals(email.from_email, self.from_address)
        self.assertEquals(email.subject, 'ShadowCon [%s]: %s' % (subject_source, subject_details))

    def test_util_no_list(self):
        with self.assertRaises(ValueError) as e:
            mail_list("subject_source", "subject_details", "message")
        self.assertEquals(e.exception.message, "Both email_list and list_name are None")

    def test_email_list_name(self):
        self.assertEquals(str(EmailList.objects.get(name="Admin")), "Admin")

    def test_email_reply_to(self):
        email = self.run_base_test("Bob <na@na.com>")
        self.assertEquals(email.reply_to, [self.from_address, "Bob <na@na.com>"])
