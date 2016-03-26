from ddt import ddt, data
from unittest import TestCase
from reversion_compare.admin import CompareVersionAdmin
from ..admin import TimeBlockAdmin, TimeSlotAdmin, ConInfoAdmin, LocationAdmin, GameAdmin, PaymentOptionAdmin


@ddt
class AdminVersionTest(TestCase):
    @data(TimeBlockAdmin, TimeSlotAdmin, ConInfoAdmin, LocationAdmin, GameAdmin, PaymentOptionAdmin)
    def test_has_versions(self, clazz):
        self.assertTrue(CompareVersionAdmin.__subclasscheck__(clazz))
