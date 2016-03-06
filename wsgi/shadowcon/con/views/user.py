from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView, UpdateView
from django.utils import timezone
from registration.backends.hmac.views import RegistrationView as BaseRegistrationView

from ..forms import NewUserForm, AttendanceForm
from ..models import BlockRegistration, Registration, get_choice
from ..utils import friendly_username, registration_open
from .common import RegistrationOpenMixin, NotOnWaitingListMixin


@login_required
def show_profile(request):
    registration = Registration.objects.filter(user=request.user)
    payment = None
    payment_received = None

    if registration:
        payment = get_choice(registration[0].payment, Registration.PAYMENT_CHOICES)
        payment_received = registration[0].payment_received

    context = {'title': " - Account Profile",
               'name': friendly_username(request.user),
               'registration_open': registration_open(),
               'payment': payment,
               'payment_received': payment_received,
               }
    return render(request, 'con/user_profile.html', context)


class AttendanceView(RegistrationOpenMixin, LoginRequiredMixin, FormView):
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

        return super(AttendanceView, self).form_valid(form)

    def get_form_kwargs(self):
        result = super(AttendanceView, self).get_form_kwargs()
        result['registration'] = Registration.objects.filter(user=self.request.user)
        result['user'] = friendly_username(self.request.user)
        return result

    def get_success_url(self):
        return reverse('con:payment')


class NewUserView(BaseRegistrationView):
    form_class = NewUserForm


class NotAlreadyPaid(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        entry = Registration.objects.filter(user=request.user)[0]
        if entry.payment_received:
            return redirect(reverse('con:user_profile'))

        return super(NotAlreadyPaid, self).dispatch(request, args, kwargs)


class PaymentView(LoginRequiredMixin, NotOnWaitingListMixin, NotAlreadyPaid, UpdateView):
    model = Registration
    fields = ['payment']
    template_name = 'con/register_payment.html'

    def get_object(self, queryset=None):
        return Registration.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse('con:user_profile')
