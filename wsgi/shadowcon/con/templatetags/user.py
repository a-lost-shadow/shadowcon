from django import template

from ..utils import get_registration

register = template.Library()


@register.inclusion_tag('con/user_attendance.html')
def user_attendance(user):
    return {'registration': get_registration(user)}
