from __future__ import unicode_literals

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.html import strip_tags
from django.conf import settings
from reversion import revisions as reversion
from datetime import datetime
import re
import pytz

from .fields import HourField


def get_absolute_url(request, relative, args):
    if settings.DEBUG:
        domain = request.get_host()
    else:
        domain = "www.shadowcon.net"
    return "http://%s%s" % (domain, reverse(relative, args=args))


def get_choice(value, choices):
    choice = filter(lambda a: a[0] == value, choices)
    if len(choice) > 0:
        return choice[0][1]
    else:
        raise ValueError("No choice found for: %s" % value)


class ConInfo(models.Model):
    date = models.DateField()
    pre_reg_deadline = models.DateField()
    game_sub_deadline = models.DateField()
    game_reg_deadline = models.DateTimeField(
        default=pytz.timezone("US/Pacific").localize(datetime(2016, 9, 15, 18, 0, 0)))
    location = models.CharField(max_length=1024)
    pre_reg_cost = models.FloatField()
    door_cost = models.FloatField()
    registration_opens = models.DateTimeField()
    max_attendees = models.PositiveIntegerField()

    def __str__(self):
        format_str = "Date: %s, Location: %s, Game Submission Deadline: %s, PreReg Deadline: %s, " + \
                     "PreReg Cost: %s, Door Cost: %s, Registration Opens: %s, Max Attendees: %s, " + \
                     "Game Registration Deadline: %s"
        return format_str % (self.date, self.location, self.game_sub_deadline,
                             self.pre_reg_deadline, self.pre_reg_cost, self.door_cost,
                             self.registration_opens, self.max_attendees, self.game_reg_deadline)


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

    def second_word(self):
        return str(self.text).split()[1].strip()

    def has_second_word(self):
        return len(str(self.text).split()) > 1

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


@reversion.register()
class Game(models.Model):
    title = models.CharField(max_length=256)
    gm = models.CharField(max_length=256)
    time_block = models.ForeignKey(TimeBlock, blank=True, null=True)
    time_slot = models.ForeignKey(TimeSlot, blank=True, null=True)
    location = models.ForeignKey(Location, blank=True, null=True)
    number_players = models.CharField(max_length=32, verbose_name="Number of Players")
    game_length = models.CharField(max_length=64, verbose_name="Game Length")
    system = models.CharField(max_length=256)
    triggers = models.CharField(max_length=256)
    description = RichTextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preferred_time = models.CharField(max_length=256, blank=True, verbose_name="Preferred Time(s)", default="")
    special_requests = models.CharField(max_length=256, blank=True, verbose_name="Special Request(s)",
                                        help_text="(e.g. preferred room)", default="")
    last_modified = models.DateTimeField()
    last_scheduled = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        format_str = "Title: %s, GM: %s, Time Block: %s, Time Slot: %s, Location: %s, " + \
                     "Game Length: %s, Number Players: %s, System: %s, Triggers: %s, User: %s, " + \
                     "Description: <CLOB>, Preferred Time: %s, Special Requests: %s, Last Modified: %s, " + \
                     "Last Scheduled: %s"
        return format_str % (self.title, self.gm, self.time_block, self.time_slot, self.location,
                             self.game_length, self.number_players, self.system, self.triggers,
                             self.user, self.preferred_time, self.special_requests,
                             self.last_modified, self.last_scheduled)

    def email_format(self, request):
        return "\n".join(["Title: %s",
                          "GM: %s",
                          "Number Players:%s",
                          "Game Length: %s",
                          "System: %s",
                          "Triggers: %s",
                          "Preferred Time(s): %s",
                          "Special Request(s): %s",
                          "",
                          "Raw Description:",
                          "%s",
                          "",
                          "HTML Description:",
                          "%s",
                          "",
                          "Admin Link:",
                          "%s"]) % (self.title, self.gm, self.number_players, self.game_length, self.system,
                                    self.triggers, self.preferred_time, self.special_requests,
                                    strip_tags(self.description), self.description,
                                    get_absolute_url(request, "admin:convention_game_change", args=(self.id,)))

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


class PaymentOption(models.Model):
    slug = models.SlugField(primary_key=True, max_length=64)
    name = models.CharField(max_length=64)
    description = RichTextField()
    button = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(PaymentOption, self).save(*args, **kwargs)


@reversion.register()
class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_date = models.DateTimeField()
    last_updated = models.DateTimeField()
    payment = models.ForeignKey(PaymentOption)
    payment_received = models.BooleanField(default=False)

    def __str__(self):
        return "User: %s, Registration Date: %s, Payment: %s, Payment Received: %s, Last Updated: %s" % \
               (self.user, self.registration_date, self.payment, self.payment_received, self.last_updated)


@reversion.register()
class BlockRegistration(models.Model):
    ATTENDANCE_MAYBE = 'M'
    ATTENDANCE_YES = 'Y'
    ATTENDANCE_NO = 'N'
    ATTENDANCE_CHOICES = (
        (ATTENDANCE_MAYBE, 'Maybe'),
        (ATTENDANCE_YES, 'Yes'),
        (ATTENDANCE_NO, 'No'),
    )
    time_block = models.CharField(max_length=64)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE)
    attendance = models.CharField(max_length=1, choices=ATTENDANCE_CHOICES, default=ATTENDANCE_YES)

    def __str__(self):
        return "Registration: %s, Time Block: %s, Attendance: %s" % \
               (self.registration,
                self.time_block,
                get_choice(self.attendance, self.ATTENDANCE_CHOICES))
