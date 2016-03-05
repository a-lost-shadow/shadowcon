from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.utils import timezone
from registration.backends.hmac.views import RegistrationView as BaseRegistrationView

from ..forms import NewUserForm, AttendanceForm
from ..models import TimeBlock, BlockRegistration, get_choice, Registration
from ..utils import friendly_username, registration_open
from .common import RegistrationOpenMixin


@login_required
def show_profile(request):
    registration = []

    registration_object = Registration.objects.filter(user=request.user)
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

    context = {'title': " - Account Profile",
               'name': friendly_username(request.user),
               'registration': registration,
               'registration_open': registration_open(),
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
        else:
            registration = registration[0]
            BlockRegistration.objects.filter(registration=registration).delete()

        registration.last_updated = timezone.now()
        registration.save()
        form.save(registration)

        return super(NewAttendanceView, self).form_valid(form)

    def get_form_kwargs(self):
        result = super(NewAttendanceView, self).get_form_kwargs()
        result['registration'] = Registration.objects.filter(user=self.request.user)
        result['user'] = friendly_username(self.request.user)
        return result

    def get_success_url(self):
        return reverse('con:user_profile')


class NewUserView(BaseRegistrationView):
    form_class = NewUserForm
