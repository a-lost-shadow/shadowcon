from django import template
from django.utils import dateformat, timezone
from datetime import date
import pytz

from ..utils import get_con_value

register = template.Library()


@register.simple_tag
def con_date():
    start = get_con_value("date")
    end = date(start.year, start.month, start.day + 2)
    return str(dateformat.format(start, "F dS - ") + dateformat.format(end, "dS, Y"))


@register.simple_tag
def con_year():
    return str(get_con_value("date").year)


@register.simple_tag
def con_pre_reg_deadline():
    return dateformat.format(get_con_value("pre_reg_deadline"), "F dS, Y")


@register.simple_tag
def con_game_sub_deadline():
    return dateformat.format(get_con_value("game_sub_deadline"), "F dS, Y")


@register.simple_tag
def con_location():
    return get_con_value("location")


@register.simple_tag
def con_door_cost():
    return "$%.2f" % get_con_value("door_cost")


@register.simple_tag
def con_pre_reg_cost():
    return "$%.2f" % get_con_value("pre_reg_cost")


@register.inclusion_tag('con/register_sidebar_links.html')
def register_links():
    raw_open_date = get_con_value("registration_opens")
    local_open_date = raw_open_date.astimezone(pytz.timezone('US/Pacific'))

    return {'registration_open': raw_open_date <= timezone.now(),
            'open_date': local_open_date.strftime("%B %d, %Y<br>%I:%M:%S %p %Z")}


@register.simple_tag
def con_registration_opens():
    raw_open_date = get_con_value("registration_opens")
    local_open_date = raw_open_date.astimezone(pytz.timezone('US/Pacific'))

    return local_open_date.strftime("%B %d, %Y at %I:%M:%S %p %Z")
