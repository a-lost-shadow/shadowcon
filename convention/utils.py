from django.utils import timezone

from .models import ConInfo, Registration, BlockRegistration, TimeBlock, get_choice, Game


def friendly_username(user):
    name = user.first_name + " " + user.last_name
    name = name.strip()
    if "" == name:
        name = user.username
    return name


def get_current_con():
    dateless_coninfos = ConInfo.objects.filter(date=None)
    if len(dateless_coninfos) == 1:
        return dateless_coninfos[0]
    if len(dateless_coninfos) > 1:
        raise ValueError("Multiple con objects with no date found, can not determine which is the current one")

    con_objects = ConInfo.objects.order_by('date').all()
    if len(con_objects) == 0:
        raise ValueError("No con object found")
    return con_objects[len(con_objects)-1]


def get_con_value(parameter):
    return getattr(get_current_con(), parameter)


def is_registration_open():
    open_date = get_con_value("registration_opens")
    return open_date is not None and open_date <= timezone.now()


def is_pre_reg_open(user):
    if user and user.id is not None:
        return len(Game.objects.filter(user=user)) > 0
    else:
        return False


def get_registration(user):
    registration = []

    convention = get_current_con()
    registration_object = Registration.objects.filter(user=user).filter(convention=convention)
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
