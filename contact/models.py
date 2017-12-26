from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import Group, User


class EmailList(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name


class GroupEmailEntry(models.Model):
    list = models.ForeignKey(EmailList, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)


class UserEmailEntry(models.Model):
    list = models.ForeignKey(EmailList, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class ContactReason(models.Model):
    name = models.CharField(max_length=256, unique=True)
    list = models.ForeignKey(EmailList, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
