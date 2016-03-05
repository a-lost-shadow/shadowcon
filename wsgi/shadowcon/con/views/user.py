from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.utils import timezone
from registration.backends.hmac.views import RegistrationView as BaseRegistrationView

from ..forms import NewUserForm, AttendanceForm
from ..models import TimeBlock, BlockRegistration, get_choice, Registration
from ..utils import friendly_username
from .common import RegistrationOpenMixin


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
            registration.append("%s: %s" % (item.time_block.text, get_choice(item.attendance,
                                                                             BlockRegistration.ATTENDANCE_CHOICES)))

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


class NewAttendanceView(RegistrationOpenMixin, LoginRequiredMixin, FormView):
    template_name = 'con/register_attendance.html'
    form_class = AttendanceForm
    model = Registration
    success_url = '/new_attend/'

    def form_valid(self, form):
        registration = Registration.objects.filter(user=self.request.user)
        if 0 == len(registration):
            registration = Registration(user=self.request.user,
                                        registration_date=timezone.now(),
                                        payment=Registration.PAYMENT_CASH)
            registration.save()
        else:
            registration = registration[0]
            BlockRegistration.objects.filter(registration=registration).delete()

        form.save(registration)

        return super(NewAttendanceView, self).form_valid(form)

    def get_form_kwargs(self):
        result = super(NewAttendanceView, self).get_form_kwargs()
        result['registration'] = Registration.objects.filter(user=self.request.user)
        result['user'] = friendly_username(self.request.user)
        return result


class NewUserView(BaseRegistrationView):
    form_class = NewUserForm
