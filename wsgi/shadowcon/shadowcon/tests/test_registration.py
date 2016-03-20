from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.template.exceptions import TemplateDoesNotExist
from django.test import Client
from shadowcon.tests.utils import ShadowConTestCase


class NewUserRegistrationTest(ShadowConTestCase):
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

        email = self.get_email()

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

        email = self.get_email()
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


# Mainly just want to test that our templates are being loaded
class PasswordResetChangeTest(ShadowConTestCase):
    def setUp(self):
        self.client = Client()

    def run_test(self, key):
        response = self.client.get(reverse(key))
        self.assertSectionContains(response, "ShadowCon 2016", "title")
        return response

    def test_login(self):
        response = self.run_test('login')
        self.assertSectionContains(response, '<p><a href="%s">%s</a></p>' % (reverse('password_reset'),
                                                                             'Lost password\\?'),
                                   'section id="main" role="main"', '/section')
        self.assertSectionContains(response, '<p><a href="%s">%s</a></p>' % (reverse('con:new_user'),
                                                                             'Create New Account'),
                                   'section id="main" role="main"', '/section')

    def test_logout(self):
        response = self.run_test('logout')
        self.assertSectionContains(response, 'You have successfully logged out',
                                   'section id="main" role="main"', '/section')

    def test_password_change(self):
        self.client.login(username="user", password="123")
        response = self.run_test('password_change')
        self.assertSectionContains(response, 'Enter new password', 'section id="main" role="main"', '/section')

    def test_password_change_done(self):
        self.client.login(username="user", password="123")
        response = self.run_test('password_change_done')
        self.assertSectionContains(response, '<h2>Password Changed</h2>', 'section id="main" role="main"', '/section')

    def test_password_reset(self):
        response = self.run_test('password_reset')
        self.assertSectionContains(response, 'Forgotten your password\\? Enter your',
                                   'section id="main" role="main"', '/section')

    def test_password_reset_done(self):
        response = self.run_test('password_reset_done')
        self.assertSectionContains(response, 'Password reset sent', 'section id="main" role="main"', '/section')

    def test_password_reset_confirm_invalid_link(self):
        response = self.client.get(reverse('password_reset_confirm', args=["invalid", "4a8-cd1bf13135ee4cae7176"]))
        self.assertSectionContains(response, "ShadowCon 2016", "title")
        self.assertSectionContains(response, 'The password reset link was invalid',
                                   'section id="main" role="main"', '/section')

    def test_password_reset_confirm_valid_link(self):
        self.client.post(reverse('password_reset'), {"email": "user@na.com"})

        email = self.get_email()
        start = str(email.body).index('/reset')
        stop = str(email.body).index('Your username, in case you\'ve forgotten: user')
        link = str(email.body)[start:stop].strip()

        response = self.client.get(link)
        self.assertSectionContains(response, "ShadowCon 2016", "title")
        self.assertSectionContains(response, 'Please enter your new password twice',
                                   'section id="main" role="main"', '/section')
