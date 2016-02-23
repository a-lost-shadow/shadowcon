from django.db.models import FloatField
from django.utils.translation import ugettext_lazy
from django.core import validators


class HourField(FloatField):
    description = ugettext_lazy("Hour of the day 0-23.99")
    default_validators = [validators.MinValueValidator(0), validators.MaxValueValidator(23.99)]
