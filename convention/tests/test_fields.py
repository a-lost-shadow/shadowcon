from django.core.exceptions import ValidationError
from ..fields import HourField
from shadowcon.tests.utils import ShadowConTestCase


class FieldsTest(ShadowConTestCase):
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

