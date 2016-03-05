from __future__ import unicode_literals

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.db import models
import re

from .fields import HourField


def get_choice(value, choices):
    choice = filter(lambda a: a[0] == value, choices)[0]
    return choice[1]


class ConInfo(models.Model):
    date = models.DateField()
    pre_reg_deadline = models.DateField()
    game_sub_deadline = models.DateField()
    location = models.CharField(max_length=1024)
    pre_reg_cost = models.FloatField()
    door_cost = models.FloatField()
    registration_opens = models.DateTimeField()
    max_attendees = models.PositiveIntegerField()

    def __str__(self):
        format_str = "date: %s, location: %s, game_sub_deadline: %s, pre_reg_deadline: %s, " + \
                     "pre_reg_cost: %s, door_cost: %s, registration_opens: %s, max_attendees: %s"
        return format_str % (self.date, self.location, self.game_sub_deadline,
                             self.pre_reg_deadline, self.pre_reg_cost, self.door_cost,
                             self.registration_opens, self.max_attendees)


weekdays = {u'monday': True,
            u'tuesday': True,
            u'wednesday': True,
            u'thursday': True,
            u'friday': True,
            u'saturday': True,
            u'sunday': True,
            }


class TimeBlock(models.Model):
    text = models.CharField(max_length=64)
    sort_id = models.IntegerField()

    def __str__(self):
        return self.text + "[" + str(self.sort_id) + "]"

    def first_word(self):
        return str(self.text).split()[0].strip()

    def get_combined(self, time_slot):
        block_first_word = self.first_word()
        if weekdays.get(unicode(block_first_word.lower()), False):
            return block_first_word + " " + str(time_slot)
        else:
            return self.text + " : " + str(time_slot)


def am_pm_print(value):
    if 0 == value:
        return "Midnight"
    if 12 == value:
        return "Noon"
    if value < 12:
        return "%d AM" % value
    else:
        return "%d PM" % (value - 12)


class TimeSlot(models.Model):
    start = HourField()
    stop = HourField()

    def __str__(self):
        return "%s - %s" % (am_pm_print(self.start), am_pm_print(self.stop))


class Location(models.Model):
    text = models.CharField(max_length=256)

    def __str__(self):
        return self.text


class Game(models.Model):
    title = models.CharField(max_length=256)
    gm = models.CharField(max_length=256)
    time_block = models.ForeignKey(TimeBlock, blank=True, null=True)
    time_slot = models.ForeignKey(TimeSlot, blank=True, null=True)
    location = models.ForeignKey(Location, blank=True, null=True,)
    number_players = models.CharField(max_length=32)
    duration = models.CharField(max_length=64)
    system = models.CharField(max_length=256)
    triggers = models.CharField(max_length=256)
    description = RichTextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        format_str = "Title: %s, GM: %s, Time Block: %s, Time Slot: %s, Location: %s, " + \
                     "Duration: %s, # Players: %s, System: %s, Triggers: %s, User: %s, " + \
                     "Description: <CLOB>"
        return format_str % (self.title, self.gm, self.time_block, self.time_slot, self.location,
                             self.duration, self.number_players, self.system, self.triggers,
                             self.user)

    def header_target(self):
        return re.sub('[^A-Za-z0-9]', '_', str(self.title).strip().lower())

    def friendly_block(self):
        if self.time_block is not None:
            return self.time_block.text
        else:
            return "Not Scheduled"

    def combined_time(self):
        if self.time_block is not None and self.time_slot is not None:
            return self.time_block.get_combined(self.time_slot)
        else:
            return "Not Scheduled"


class Registration(models.Model):
    PAYMENT_CASH = 'C'
    PAYMENT_QUICK_PAY = 'Q'
    PAYMENT_PAYPAL = 'P'
    PAYMENT_VENMO = 'V'
    PAYMENT_CHOICES = (
        (PAYMENT_CASH, 'Paying by Cash'),
        (PAYMENT_QUICK_PAY, 'Chase Quick Pay'),
        (PAYMENT_PAYPAL, 'Paying by Venmo'),
        (PAYMENT_VENMO, 'Paying by Paypal'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_date = models.DateTimeField()
    last_updated = models.DateTimeField()
    payment = models.CharField(max_length=1, choices=PAYMENT_CHOICES)
    payment_received = models.BooleanField(default=False)

    def __str__(self):
        return "user: %s, registration_date: %s, payment: %s" % \
               (self.user, self.registration_date, get_choice(self.payment, self.PAYMENT_CHOICES))


class BlockRegistration(models.Model):
    ATTENDANCE_MAYBE = 'M'
    ATTENDANCE_YES = 'Y'
    ATTENDANCE_NO = 'N'
    ATTENDANCE_CHOICES = (
        (ATTENDANCE_MAYBE, 'Maybe'),
        (ATTENDANCE_YES, 'Yes'),
        (ATTENDANCE_NO, 'No'),
    )
    time_block = models.ForeignKey(TimeBlock, on_delete=models.CASCADE)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    attendance = models.CharField(max_length=1, choices=ATTENDANCE_CHOICES, default=ATTENDANCE_YES)

    def __str__(self):
        return "registration: %s, time_block: %s, attendance: %s" % \
               (self.registration,
                self.time_block,
                get_choice(self.attendance, self.ATTENDANCE_CHOICES))
