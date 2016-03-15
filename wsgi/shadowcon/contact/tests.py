from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from shadowcon.tests.utils import SectionCheckMixIn

from .utils import mail_list
from .models import EmailList


class ContactTest(SectionCheckMixIn, TestCase):
    fixtures = ['auth', 'initial']
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

    def test_success_email(self):
        self.client.post(self.url, self.test_data)

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEquals(email.body, self.test_data['message'])
        self.assertEquals(email.to, ['staff@na.com', 'admin@na.com'])
        self.assertEquals(email.from_email, "%s <%s>" % (self.test_data['name'], self.test_data['email']))
        self.assertEquals(email.subject, 'ShadowCon [Something Broke]: %s' % self.test_data['summary'])

    def run_unclean_test(self, key):
        new_data = self.test_data.copy()
        new_data[key] = "<a>%s</a>" % self.test_data[key]

        self.client.post(self.url, new_data)

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEquals(email.body, self.test_data['message'])
        self.assertEquals(email.to, ['staff@na.com', 'admin@na.com'])
        self.assertEquals(email.from_email, "%s <%s>" % (self.test_data['name'], self.test_data['email']))
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

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEquals(email.body, 'My precious')
        self.assertEquals(email.to, ['user@na.com'])
        self.assertEquals(email.from_email, "Different Name <na@na.net>")
        self.assertEquals(email.subject, 'ShadowCon [Admins make things better]: A summary goes here')

    def test_util(self):
        subject_source = "Itch"
        subject_details = "In my brain"
        message = "I can't scratch it"
        sender = "Crazy It <i.am.crazy@gmail.com"
        mail_list(subject_source, subject_details, message, sender, EmailList.objects.get(name="Admin"))

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEquals(email.body, message)
        self.assertEquals(email.to, ['user@na.com'])
        self.assertEquals(email.from_email, sender)
        self.assertEquals(email.subject, 'ShadowCon [%s]: %s' % (subject_source, subject_details))

    def test_util_alternate(self):
        subject_source = "World Domination"
        subject_details = "Is at hand"
        message = "Now only $5.95"
        sender = "Russia with Love <007@mi6.co.uk>"
        mail_list(subject_source, subject_details, message, sender, list_name="Website")

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEquals(email.body, message)
        self.assertEquals(email.to, ['staff@na.com', 'admin@na.com'])
        self.assertEquals(email.from_email, sender)
        self.assertEquals(email.subject, 'ShadowCon [%s]: %s' % (subject_source, subject_details))
