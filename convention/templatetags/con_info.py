from django import template
from django.utils import dateformat, html
from datetime import date
import pytz

from ..utils import get_con_value, is_pre_reg_open, is_registration_open
from ..models import Trigger

register = template.Library()


@register.simple_tag
def con_date():
    start = get_con_value("date")
    end = date(start.year, start.month, start.day + 2)
    return str(dateformat.format(start, "F jS - ") + dateformat.format(end, "jS, Y"))


@register.simple_tag
def con_year():
    return str(get_con_value("date").year)


@register.simple_tag
def con_pre_reg_deadline():
    return dateformat.format(get_con_value("pre_reg_deadline"), "F jS, Y")


@register.simple_tag
def con_game_sub_deadline():
    return dateformat.format(get_con_value("game_sub_deadline"), "F jS, Y")


@register.simple_tag
def con_game_reg_deadline():
    return html.format_html(get_datetime_as_string(get_con_value("game_reg_deadline"), "<br />"))


@register.simple_tag
def con_location():
    return get_con_value("location")


@register.simple_tag
def con_door_cost():
    return "$%.2f" % get_con_value("door_cost")


@register.simple_tag
def con_pre_reg_cost():
    return "$%.2f" % get_con_value("pre_reg_cost")


def get_datetime_as_string(value, date_time_sep):
    local = value.astimezone(pytz.timezone('US/Pacific'))
    return dateformat.format(local, "F jS, Y") + date_time_sep + dateformat.format(local, "g:i:s A T")


@register.inclusion_tag('convention/register_sidebar_links.html')
def register_links(user):
    raw_open_date = get_con_value("registration_opens")

    return {'is_registration_open': is_registration_open(),
            'is_pre_reg_open': is_pre_reg_open(user),
            'open_date': get_datetime_as_string(raw_open_date, "<br>")}


@register.simple_tag
def con_registration_opens():
    return get_datetime_as_string(get_con_value("registration_opens"), " at ")


@register.inclusion_tag('convention/trigger_list.html')
def triggers_as_list():
    return {'triggers': sorted([x.text for x in Trigger.objects.all()])}
