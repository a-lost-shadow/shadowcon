from django import template
from django.utils import dateformat, timezone
from datetime import date
import pytz

from ..models import Game
from ..utils import get_con_value

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
def con_location():
    return get_con_value("location")


@register.simple_tag
def con_door_cost():
    return "$%.2f" % get_con_value("door_cost")


@register.simple_tag
def con_pre_reg_cost():
    return "$%.2f" % get_con_value("pre_reg_cost")


def get_registration_open_string(raw_open_date, date_time_sep):
    local = raw_open_date.astimezone(pytz.timezone('US/Pacific'))
    return dateformat.format(local, "F jS, Y") + date_time_sep + dateformat.format(local, "g:i:s A T")


@register.inclusion_tag('con/register_sidebar_links.html')
def register_links(user):
    raw_open_date = get_con_value("registration_opens")
    is_registration_open = raw_open_date <= timezone.now()
    if user and user.id is not None:
        is_pre_reg_open = len(Game.objects.filter(user=user)) > 0
    else:
        is_pre_reg_open = False

    return {'is_registration_open': is_registration_open,
            'is_pre_reg_open': is_pre_reg_open,
            'open_date': get_registration_open_string(raw_open_date, "<br>")}


@register.simple_tag
def con_registration_opens():
    return get_registration_open_string(get_con_value("registration_opens"), " at ")
