from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from .models import EmailList, GroupEmailEntry, UserEmailEntry, ContactReason


class GroupInline(admin.TabularInline):
    model = GroupEmailEntry
    extra = 2


class UserInline(admin.TabularInline):
    model = UserEmailEntry
    extra = 2


@admin.register(EmailList)
class EmailListAdmin(CompareVersionAdmin):
    inlines = [GroupInline, UserInline]
    list_display = ['name']


@admin.register(ContactReason)
class ContactReasonAdmin(CompareVersionAdmin):
    list_display = ['name', 'list']
