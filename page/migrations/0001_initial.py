# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-22 06:28
from __future__ import unicode_literals

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('url', models.CharField(max_length=256)),
                ('content', ckeditor.fields.RichTextField()),
            ],
        ),
    ]