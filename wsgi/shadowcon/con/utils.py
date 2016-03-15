from django.utils import timezone

from .models import ConInfo, Registration, BlockRegistration, TimeBlock, get_choice


def friendly_username(user):
    name = user.first_name + " " + user.last_name
    name = name.strip()
    if "" == name:
        name = user.username
    return name


def get_con_value(parameter):
    con_objects = ConInfo.objects.all()
    if len(con_objects) == 0:
        raise ValueError("No con object found")
    elif len(con_objects) > 1:
        raise ValueError("Multiple con objects found")

    info = con_objects[0]
    return getattr(info, parameter)


def registration_open():
    open_date = get_con_value("registration_opens")
    return open_date <= timezone.now()


def get_registration(user):
    registration = []

    registration_object = Registration.objects.filter(user=user)
    if registration_object:
        item_dict = {}
        for item in BlockRegistration.objects.filter(registration=registration_object):
            item_dict[item.time_block] = item
            if item.attendance != BlockRegistration.ATTENDANCE_NO:
                registration.append("%s: %s" % (item.time_block, get_choice(item.attendance,
                                                                            BlockRegistration.ATTENDANCE_CHOICES)))

        for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
            if time_block.text not in item_dict:
                registration.append("<b>Partially Registered: Please re-register</b>")
                break
    else:
        registration.append("Not Registered")

    return registration
