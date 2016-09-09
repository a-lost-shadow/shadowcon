from django import template
from django.core.urlresolvers import reverse
from django.utils import html

from ..utils import get_registration
from ..models import Registration

register = template.Library()


@register.inclusion_tag('convention/user_attendance.html')
def user_attendance(user):
    return {'registration': get_registration(user)}


@register.simple_tag
def admin_link(user):
    if (user.is_staff or user.is_superuser) and user.is_active:
        return html.format_html('<li><a href="{}">Admin</a></li>',
                                reverse('admin:index'))
    else:
        return ""


@register.simple_tag
def edit_schedule_link(user):
    if (user.is_staff or user.is_superuser) and user.is_active:
        return html.format_html('<li><a href="{}">Change Schedule</a></li>',
                                reverse('convention:edit_schedule'))
    else:
        return ""


@register.simple_tag
def attendance_list_link(user):
    if (user.is_staff or user.is_superuser) and user.is_active:
        return html.format_html('<li><a href="{}">View Attendance</a></li>',
                                reverse('convention:attendance_list'))
    else:
        return ""


@register.simple_tag
def game_registration_link(user):
    registration_object = Registration.objects.filter(user=user)
    if registration_object:
        return html.format_html('<li><a href="https://goo.gl/forms/xKWoC8boOUIFi32U2">Game Registration</a></li>')
    else:
        return ""
