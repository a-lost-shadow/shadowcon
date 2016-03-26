from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin
from .models import Page, Tag


@admin.register(Page)
class PageAdmin(CompareVersionAdmin):
    model = Page
    list_display = ('name', 'url')


@admin.register(Tag)
class TagAdmin(CompareVersionAdmin):
    model = Tag
