from django.contrib.auth.models import User
from django.test import TestCase, Client
from shadowcon.tests.utils import SectionCheckMixIn
from ..utils import *
from datetime import timedelta
from django.utils import timezone


class UtilsTest(SectionCheckMixIn, TestCase):
    fixtures = ['auth', 'initial']

    def setUp(self):
        self.client = Client()

    def test_friendly_username_no_first_last(self):
        user = User(username="username")
        self.assertEquals(friendly_username(user), "username")

    def test_friendly_username_first(self):
        user = User(username="username", first_name="first")
        self.assertEquals(friendly_username(user), "first")

    def test_friendly_username_last(self):
        user = User(username="username", last_name="last")
        self.assertEquals(friendly_username(user), "last")

    def test_friendly_username_full_name(self):
        user = User(username="username", first_name="first", last_name="last")
        self.assertEquals(friendly_username(user), "first last")

    def test_con_value_no_con(self):
        for con in ConInfo.objects.all():
            con.delete()

        with self.assertRaises(ValueError) as e:
            get_con_value('invalid')
        self.assertEquals(e.exception.message, "No con object found")

    def test_con_value_multi_con_objects(self):
        ConInfo(date=timezone.now(), pre_reg_deadline=timezone.now(), game_sub_deadline=timezone.now(), location="here",
                pre_reg_cost=5, door_cost=6, registration_opens=timezone.now(), max_attendees=10).save()

        with self.assertRaises(ValueError) as e:
            get_con_value('invalid')
        self.assertEquals(e.exception.message, "Multiple con objects found")

    def test_con_value_invalid_attribute(self):
        with self.assertRaises(AttributeError) as e:
            get_con_value('invalid')
        self.assertEquals(e.exception.message, "'ConInfo' object has no attribute 'invalid'")

    def test_con_value_valid_attribute(self):
        self.assertEquals(get_con_value('date'), ConInfo.objects.all()[0].date)

    def test_con_value_valid_attribute_alternate_value(self):
        now = timezone.now()
        con = ConInfo.objects.all()[0]
        con.date = now
        con.save()
        self.assertEquals(get_con_value('date'), now.date())

    def test_registration_closed(self):
        con = ConInfo.objects.all()[0]
        con.registration_open = timezone.now() + timedelta(minutes=1)
        con.save()
        self.assertEquals(registration_open(), True)

    def test_registration_open(self):
        con = ConInfo.objects.all()[0]
        con.registration_open = timezone.now() - timedelta(minutes=1)
        con.save()
        self.assertEquals(registration_open(), True)

    def test_get_registration_null(self):
        self.assertEquals(get_registration(None), ["Not Registered"])

    def test_get_registration_not_registered(self):
        self.assertEquals(get_registration(User.objects.get(username="user")), ["Not Registered"])

    def test_get_registration_fully_registered(self):
        self.assertEquals(get_registration(User.objects.get(username="staff")),
                          ['Friday Night: Maybe',
                           'Friday Midnight: Maybe',
                           'Saturday Morning: Maybe',
                           'Saturday Afternoon: Maybe',
                           'Saturday Evening: Maybe',
                           'Saturday Midnight: Maybe'])

    def test_get_registration_partially_registered(self):
        registration_object = Registration.objects.filter(user=User.objects.get(username="staff"))
        BlockRegistration.objects.filter(registration=registration_object)[0].delete()
        self.assertEquals(get_registration(User.objects.get(username="staff")),
                          ['Friday Midnight: Maybe',
                           'Saturday Morning: Maybe',
                           'Saturday Afternoon: Maybe',
                           'Saturday Evening: Maybe',
                           'Saturday Midnight: Maybe',
                           '<b>Partially Registered: Please re-register</b>'])
