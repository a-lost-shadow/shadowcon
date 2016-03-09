from django.contrib import admin
from .models import Page, Tag


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    model = Page
    list_display = ('name', 'url')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    model = Tag
