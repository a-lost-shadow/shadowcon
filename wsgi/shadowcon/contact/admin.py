from django.contrib import admin

from .models import EmailList, GroupEmailEntry, UserEmailEntry, ContactReason


class GroupInline(admin.TabularInline):
    model = GroupEmailEntry
    extra = 2


class UserInline(admin.TabularInline):
    model = UserEmailEntry
    extra = 2


@admin.register(EmailList)
class EmailListAdmin(admin.ModelAdmin):
    inlines = [GroupInline, UserInline]
    list_display = ['name']


@admin.register(ContactReason)
class ContactReasonAdmin(admin.ModelAdmin):
    list_display = ['name', 'list']
