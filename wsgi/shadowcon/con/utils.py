from django.utils import timezone

from .models import ConInfo


def friendly_username(user):
    name = user.first_name + " " + user.last_name
    if "" == name.strip():
        name = user.username
    return name


def get_con_value(parameter):
    con_objects = ConInfo.objects.all()
    if len(con_objects) == 0:
        return "No con object found"
    elif len(con_objects) > 1:
        return "Multiple con objects found"

    info = con_objects[0]
    return getattr(info, parameter)


def registration_open():
    open_date = get_con_value("registration_opens")
    return open_date <= timezone.now()
