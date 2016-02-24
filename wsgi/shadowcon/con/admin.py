from django.contrib import admin
from .models import TimeBlock, TimeSlot, ConInfo, Location, Game


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    model = TimeSlot
    list_display = ('text', 'sort_id')
    ordering = ['sort_id']


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    model = TimeSlot
    ordering = ['start', 'stop']


@admin.register(ConInfo)
class ConInfoAdmin(admin.ModelAdmin):
    model = ConInfo
    list_display = ('date', 'location', 'pre_reg_deadline', 'game_sub_deadline')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    model = Location


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    model = Game
    list_display = ('title', 'gm', 'time_block', 'time_slot', 'location')
