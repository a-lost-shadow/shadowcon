from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView, UpdateView
from registration.backends.hmac.views import RegistrationView as BaseRegistrationView

from ..forms import NewUserForm, AttendanceForm
from ..models import Registration, PaymentOption
from ..utils import friendly_username, is_registration_open, is_pre_reg_open
from .common import RegistrationOpenMixin, NotOnWaitingListMixin


@login_required
def show_profile(request):
    registration = Registration.objects.filter(user=request.user)
    payment = None
    payment_received = None

    if registration:
        payment = registration[0].payment
        payment_received = registration[0].payment_received

    context = {'name': friendly_username(request.user),
               'is_registration_open': is_registration_open(),
               'is_pre_reg_open': is_pre_reg_open(request.user),
               'payment': payment,
               'payment_received': payment_received,
               }
    return render(request, 'con/user_profile.html', context)


class AttendanceView(RegistrationOpenMixin, LoginRequiredMixin, FormView):
    template_name = 'con/register_attendance.html'
    form_class = AttendanceForm

    def form_valid(self, form):
        form.save()
        return super(AttendanceView, self).form_valid(form)

    def get_form_kwargs(self):
        result = super(AttendanceView, self).get_form_kwargs()
        result['user'] = self.request.user
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

    def get_context_data(self, **kwargs):
        if 'payment_options' not in kwargs:
            kwargs['payment_options'] = PaymentOption.objects.all()
        return super(PaymentView, self).get_context_data(**kwargs)
