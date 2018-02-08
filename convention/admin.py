from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin
from .models import TimeBlock, TimeSlot, ConInfo, Location, Game, PaymentOption, BlockRegistration, Registration
from .models import Trigger, Referral


@admin.register(TimeBlock)
class TimeBlockAdmin(CompareVersionAdmin):
    model = TimeSlot
    list_display = ('text', 'sort_id')
    ordering = ['sort_id']


@admin.register(TimeSlot)
class TimeSlotAdmin(CompareVersionAdmin):
    model = TimeSlot
    ordering = ['start', 'stop']


@admin.register(ConInfo)
class ConInfoAdmin(CompareVersionAdmin):
    model = ConInfo
    list_display = ('date', 'location', 'pre_reg_deadline', 'game_sub_deadline')


@admin.register(Location)
class LocationAdmin(CompareVersionAdmin):
    model = Location


@admin.register(Game)
class GameAdmin(CompareVersionAdmin):
    model = Game
    list_display = ('title', 'gm', 'time_block', 'time_slot', 'location')


@admin.register(PaymentOption)
class PaymentOptionAdmin(CompareVersionAdmin):
    model = PaymentOption
    exclude = ['slug']


@admin.register(BlockRegistration)
class BlockRegistrationAdmin(CompareVersionAdmin):
    model = BlockRegistration


@admin.register(Registration)
class RegistrationAdmin(CompareVersionAdmin):
    model = Registration


@admin.register(Trigger)
class TriggerAdmin(CompareVersionAdmin):
    model = Trigger


@admin.register(Referral)
class ReferralAdmin(CompareVersionAdmin):
    model = Referral
    ordering = ['user']
    readonly_fields = ['code']
