from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.template.exceptions import TemplateDoesNotExist
from django.test import TestCase, Client
from shadowcon.tests.utils import SectionCheckMixIn


class NewUserRegistrationTest(SectionCheckMixIn, TestCase):
    fixtures = ['auth', 'initial']

    def setUp(self):
        self.client = Client()
        self.registration_data = {"username": "username",
                                  "first_name": "first",
                                  "last_name": "last",
                                  "email": "test@test.com",
                                  "password1": "Not1A2Common3Password",
                                  "password2": "Not1A2Common3Password",
                                  }

    def test_get_registration_form(self):
        response = self.client.get(reverse('con:new_user'))
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, "Create New Account", "h2")
        self.assertSectionContains(response, "ShadowCon 2016", "title")

    def test_new_user_submit_redirect(self):
        response = self.client.post(reverse('con:new_user'), self.registration_data)
        self.assertRedirects(response, reverse('registration_complete'))

    def test_new_user_email(self):
        self.client.post(reverse('con:new_user'), self.registration_data)

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEquals(email.subject, "Verify your account with ShadowCon")
        self.assertEquals(email.from_email, "webmaster@localhost")
        self.assertEquals(len(email.to), 1)
        self.assertEquals(email.to[0], self.registration_data["email"])
        self.assertGreater(str(email.body).find("In order to activate your account, please go to"), -1)

    def test_new_user_model(self):
        self.client.post(reverse('con:new_user'), self.registration_data)
        user = User.objects.get(username="username")
        self.assertEquals(user.first_name, "first")
        self.assertEquals(user.last_name, "last")
        self.assertEquals(user.email, "test@test.com")
        self.assertEquals(user.is_active, False)
        self.assertEquals(user.is_staff, False)
        self.assertEquals(user.is_superuser, False)

    def test_get_activation_sent(self):
        response = self.client.get(reverse('registration_complete'))
        self.assertSectionContains(response, "Activation e-mail sent", "h2")
        self.assertSectionContains(response, "ShadowCon 2016", "title")

    def get_activate_link(self):
        self.client.post(reverse('con:new_user'), self.registration_data)

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]
        start = str(email.body).index('/accounts/activate')
        stop = str(email.body).index('This link will expire')
        return str(email.body)[start:stop].strip()

    def test_activate_redirect(self):
        link = self.get_activate_link()
        response = self.client.get(link)
        self.assertRedirects(response, reverse('registration_activation_complete'))

    def test_activation_complete(self):
        response = self.client.get(reverse('registration_activation_complete'))
        self.assertSectionContains(response, "Activation Complete", "h2")
        self.assertSectionContains(response, "ShadowCon 2016", "title")

    def test_activate_model(self):
        link = self.get_activate_link()
        self.client.get(link)
        user = User.objects.get(username="username")
        self.assertEquals(user.is_active, True)

    def test_bad_activation_link(self):
        link = list(self.get_activate_link())
        link[5] = chr(ord(link[5]) + 1)
        response = self.client.get(str(link))
        self.assertEquals(response.status_code, 404)

    def test_activation_link_used_twice(self):
        link = self.get_activate_link()
        response = self.client.get(link)
        self.assertRedirects(response, reverse('registration_activation_complete'))
        with self.assertRaises(TemplateDoesNotExist) as e:
            self.client.get(link)
        self.assertEquals(e.exception.message, "registration/activate.html")
