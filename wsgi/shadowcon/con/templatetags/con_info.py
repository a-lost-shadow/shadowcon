from django import template
from django.utils import dateformat, html
from django.core.urlresolvers import reverse
from datetime import date

from ..models import ConInfo

register = template.Library()


def get_value(parameter):
    con_objects = ConInfo.objects.all()
    if len(con_objects) == 0:
        return "No con object found"
    elif len(con_objects) > 1:
        return "Multiple con objects found"

    info = con_objects[0]
    return getattr(info, parameter)


@register.simple_tag
def con_date():
    start = get_value("date")
    end = date(start.year, start.month, start.day + 2)
    return str(dateformat.format(start, "F dS - ") + dateformat.format(end, "dS, Y"))


@register.simple_tag
def con_year():
    return str(get_value("date").year)


@register.simple_tag
def con_pre_reg_deadline():
    return dateformat.format(get_value("pre_reg_deadline"), "F dS, Y")


@register.simple_tag
def con_game_sub_deadline():
    return dateformat.format(get_value("game_sub_deadline"), "F dS, Y")


@register.simple_tag
def con_location():
    return get_value("location")


@register.simple_tag
def con_door_cost():
    return "$%.2f" % get_value("door_cost")


@register.simple_tag
def con_pre_reg_cost():
    return "$%.2f" % get_value("pre_reg_cost")


@register.simple_tag
def admin_link(user):
    if (user.is_staff or user.is_admin) and user.is_active:
        return html.format_html("<li><a href='{}'>Admin</a></li>",
                                reverse('admin:index'))
    else:
        return ""
