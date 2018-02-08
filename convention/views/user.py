from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView, UpdateView
from django.views.generic import TemplateView
from registration.backends.hmac.views import RegistrationView as BaseRegistrationView

from ..forms import NewUserForm, AttendanceForm
from ..models import Registration, PaymentOption, BlockRegistration, TimeBlock, get_choice, Referral
from ..utils import friendly_username, is_registration_open, is_pre_reg_open
from .common import RegistrationOpenMixin, NotOnWaitingListMixin, IsStaffMixin


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
    return render(request, 'convention/user_profile.html', context)


class AttendanceView(RegistrationOpenMixin, LoginRequiredMixin, FormView):
    template_name = 'convention/register_attendance.html'
    form_class = AttendanceForm

    def form_valid(self, form):
        form.save()
        return super(AttendanceView, self).form_valid(form)

    def get_form_kwargs(self):
        result = super(AttendanceView, self).get_form_kwargs()
        result['user'] = self.request.user
        return result

    def get_success_url(self):
        return reverse('convention:payment')


def registration_count(time_block, attendance):
    return str(len(BlockRegistration.objects.filter(time_block=time_block.text).filter(attendance__exact=attendance)))


def missing_count(time_block):
    return str(len(Registration.objects.all()) - len(BlockRegistration.objects.filter(time_block=time_block.text)))


class AttendanceList(LoginRequiredMixin, IsStaffMixin, TemplateView):
    template_name = 'convention/attendance_list.html'

    def get_context_data(self, **kwargs):
        time_blocks = TimeBlock.objects.exclude(text__startswith='Not').order_by('sort_id')

        header = "<th></th>"
        yes = "<td>" + get_choice(BlockRegistration.ATTENDANCE_YES, BlockRegistration.ATTENDANCE_CHOICES) + "</td>"
        maybe = "<td>" + get_choice(BlockRegistration.ATTENDANCE_MAYBE, BlockRegistration.ATTENDANCE_CHOICES) + "</td>"
        no = "<td>" + get_choice(BlockRegistration.ATTENDANCE_NO, BlockRegistration.ATTENDANCE_CHOICES) + "</td>"
        missing = "<td>Missing</td>"

        if 'totals' not in kwargs:
            for block in time_blocks:
                header += "<th>" + block.text + "</th>"
                yes += "<td>" + registration_count(block, BlockRegistration.ATTENDANCE_YES) + "</td>"
                maybe += "<td>" + registration_count(block, BlockRegistration.ATTENDANCE_MAYBE) + "</td>"
                no += "<td>" + registration_count(block, BlockRegistration.ATTENDANCE_NO) + "</td>"
                missing += "<td>" + missing_count(block) + "</td>"
            kwargs['totals'] = "\n  <tr>" + header + "</tr>\n  <tr>" + yes + "</tr>\n  <tr>" + maybe + \
                               "</tr>\n  <tr>" + no + "</tr>\n  <tr>" + missing + "</tr>\n"

        if 'details' not in kwargs:
            details = "\n  <tr>" + header + "</tr>"
            for entry in Registration.objects.all():
                details += "\n  <tr><td>" + friendly_username(entry.user) + "</td>"
                reg_entries = {}
                for reg in BlockRegistration.objects.filter(registration=entry):
                    reg_entries[reg.time_block] = reg.attendance

                for block in time_blocks:
                    if block.text in reg_entries:
                        details += "<td>" + get_choice(reg_entries[block.text],
                                                       BlockRegistration.ATTENDANCE_CHOICES) + "</td>"
                    else:
                        details += "<td>Missing</td>"

                details += "</tr>"
            kwargs['details'] = details + "\n"

        if 'payments' not in kwargs:
            payments = "\n  <tr><th></th><th>Donation Option</th><th>Donation Received</th></tr>"
            for entry in Registration.objects.all():
                received = "Yes" if entry.payment_received else "No"
                payments += "\n  <tr><td>" + friendly_username(entry.user) + "</td>" + "<td>" + entry.payment.name + \
                            "</td>" + "<td>" + received + "</td></tr>"
            kwargs['payments'] = payments + "\n"

        if 'contact_info' not in kwargs:
            contact_info = "\n  <tr><th>Name</th><th>Username</th><th>E-mail</th><th>Registered</th></tr>"
            for entry in User.objects.all():
                registered = "No"
                if Registration.objects.filter(user=entry):
                    registered = "Yes"
                contact_info += "\n  <tr><td>" + entry.first_name + " " + entry.last_name + "</td><td>" + \
                                entry.username + "</td><td>" + entry.email + "</td><td>" + registered + "</td></tr>"
            kwargs['contact_info'] = contact_info + "\n"

        return super(AttendanceList, self).get_context_data(**kwargs)


class NewUserView(BaseRegistrationView):
    form_class = NewUserForm

    def form_valid(self, form):
        redirect = super(NewUserView, self).form_valid(form)

        code = form.cleaned_data.get('referral_code')
        if code != "":
            referral = Referral.objects.filter(code=code)[0]
            referral.referred_user = form.instance
            referral.save()

        return redirect


class NotAlreadyPaid(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        entry = Registration.objects.filter(user=request.user)[0]
        if entry.payment_received:
            return redirect(reverse('convention:user_profile'))

        return super(NotAlreadyPaid, self).dispatch(request, args, kwargs)


class PaymentView(LoginRequiredMixin, NotOnWaitingListMixin, NotAlreadyPaid, UpdateView):
    model = Registration
    fields = ['payment']
    template_name = 'convention/register_payment.html'

    def get_object(self, queryset=None):
        return Registration.objects.get(user=self.request.user)

    def get_success_url(self):
        return reverse('convention:user_profile')

    def get_context_data(self, **kwargs):
        if 'payment_options' not in kwargs:
            kwargs['payment_options'] = PaymentOption.objects.all()
        return super(PaymentView, self).get_context_data(**kwargs)
