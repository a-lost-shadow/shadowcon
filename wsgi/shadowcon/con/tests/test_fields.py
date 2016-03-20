from django.core.exceptions import ValidationError
from django.test import TestCase
from ..fields import HourField


class FieldsTest(TestCase):
    fixtures = ['auth', 'initial']

    def test_hour_field_valid(self):
        field = HourField()
        field.run_validators(5)

    def test_hour_field_invalid_low(self):
        field = HourField()
        with self.assertRaises(ValidationError) as e:
            field.run_validators(-5)
        self.assertEquals(e.exception.messages[0],
                          "Ensure this value is greater than or equal to 0.")

    def test_hour_field_invalid_high(self):
        field = HourField()
        with self.assertRaises(ValidationError) as e:
            field.run_validators(24)
        self.assertEquals(e.exception.messages[0],
                          "Ensure this value is less than or equal to 23.99.")

