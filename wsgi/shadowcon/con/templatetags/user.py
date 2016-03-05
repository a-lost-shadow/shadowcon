from django import template

from ..models import BlockRegistration, Registration, TimeBlock, get_choice

register = template.Library()


@register.inclusion_tag('con/user_attendance.html')
def user_attendance(user):
    registration = []

    registration_object = Registration.objects.filter(user=user)
    if registration_object:
        item_dict = {}
        for item in BlockRegistration.objects.filter(registration=registration_object):
            item_dict[item.time_block] = item
            if item.attendance != BlockRegistration.ATTENDANCE_NO:
                registration.append("%s: %s" %
                                    (item.time_block.text, get_choice(item.attendance,
                                                                      BlockRegistration.ATTENDANCE_CHOICES)))

        for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
            if time_block not in item_dict:
                registration.append("<b>Partially Registered: Please re-register</b>")
                break
    else:
        registration.append("Not Registered")

    return {'registration': registration,
            }
