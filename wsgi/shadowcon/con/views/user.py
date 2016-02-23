from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.core.urlresolvers import reverse
from registration.backends.hmac.views import RegistrationView as BaseRegistrationView

from ..forms import RegistrationForm
from ..models import TimeBlock, BlockRegistration
from ..utils import friendly_username


def get_choice(block_registration):
    choice = filter(lambda a: a[0] == block_registration.attendance, BlockRegistration.ATTENDANCE_CHOICES)[0]
    return choice[1]


def get_registration(user):
    return BlockRegistration.objects.filter(user=user,
                                            attendance__in=[BlockRegistration.ATTENDANCE_YES,
                                                            BlockRegistration.ATTENDANCE_MAYBE])


@login_required
def show_profile(request):
    registration = []
    item_dict = {}
    for item in BlockRegistration.objects.filter(user=request.user):
        item_dict[item.time_block] = item
        if item.attendance != BlockRegistration.ATTENDANCE_NO:
            registration.append("%s: %s" % (item.time_block.text, get_choice(item)))

    for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
        if time_block not in item_dict:
            if 0 == len(registration):
                registration.append("Not Registered")
            else:
                registration.append("<b>Partially Registered: Please re-register</b>")
            break

    if 0 == len(registration):
        registration.append("Not Attending")

    context = {'title': " - Account Profile",
               'name': friendly_username(request.user),
               'registration': registration,
               }
    return render(request, 'con/user_profile.html', context)


@login_required
def register(request):
    item_dict = {}
    for item in BlockRegistration.objects.filter(user=request.user):
        item_dict[item.time_block] = item

    if 'POST' == request.method:
        for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
            if time_block not in item_dict:
                reg = BlockRegistration(user=request.user,
                                        time_block=time_block,
                                        attendance=request.POST[time_block.text])
                reg.save()
            else:
                item_dict[time_block].attendance = request.POST[time_block.text]
                item_dict[time_block].save()
                del item_dict[time_block]

        for item in item_dict.values():
            print "deleting " + str(item)
            item.delete()

        return HttpResponseRedirect(reverse('con:user_profile'))
    else:
        action = "Updating Registration"
        items = []
        for time_block in TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id'):
            if time_block not in item_dict:
                items.append(BlockRegistration(user=request.user, time_block=time_block))
                action = "Initial Registration"
            else:
                items.append(item_dict[time_block])

        context = {'title': ' - Register',
                   'name': friendly_username(request.user),
                   'action': action,
                   'items': items,
                   'choices': BlockRegistration.ATTENDANCE_CHOICES,
                   }
        return render(request, 'con/register_attendance.html', context)


class RegistrationView(BaseRegistrationView):
    form_class = RegistrationForm
