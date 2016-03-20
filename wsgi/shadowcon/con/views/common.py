from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import render

from ..models import Registration
from ..utils import is_registration_open, get_con_value


class RegistrationOpenMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not is_registration_open():
            return render(request, 'con/registration_not_open.html', {})
        return super(RegistrationOpenMixin, self).dispatch(request, args, kwargs)


class IsStaffMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff and not request.user.is_superuser:
            return render(request, 'con/not_staff.html', {})
        return super(IsStaffMixin, self).dispatch(request, args, kwargs)


class NotOnWaitingListMixin(AccessMixin):
    waiting_list_template = 'con/registration_wait_list.html'

    def dispatch(self, request, *args, **kwargs):
        entries = Registration.objects.order_by('registration_date')
        found = False
        for i in range(0, len(entries)):
            entry = entries[i]
            if request.user == entry.user:
                found = True
                if i >= get_con_value('max_attendees'):
                    return render(request, self.waiting_list_template, {})
                break
        if not found:
            return render(request, 'con/registration_not_found.html', {})

        return super(NotOnWaitingListMixin, self).dispatch(request, args, kwargs)
