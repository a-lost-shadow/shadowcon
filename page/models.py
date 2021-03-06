from __future__ import unicode_literals
from django.db import models
from ckeditor.fields import RichTextField


class Page(models.Model):
    name = models.CharField(max_length=256)
    url = models.CharField(max_length=256)
    content = RichTextField()

    def __str__(self):
        return self.name


class Tag(models.Model):
    tag = models.SlugField(max_length=64, primary_key=True)
    content = models.TextField()

    def __str__(self):
        return self.tag
