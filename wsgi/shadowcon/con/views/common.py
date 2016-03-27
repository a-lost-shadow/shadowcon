from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import render
from reversion import revisions as reversion

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


def is_on_wait_list(entries, request):
    found = False
    for i in range(0, len(entries)):
        entry = entries[i]
        if request.user == entry.user:
            found = True
            if i >= get_con_value('max_attendees'):
                return True
            break
    if not found:
        raise ValueError('User registration not found')

    return False


class NotOnWaitingListMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        try:
            if is_on_wait_list(Registration.objects.order_by('registration_date'), request):
                return render(request, 'con/registration_wait_list.html', {})
        except ValueError:
            return render(request, 'con/registration_not_found.html', {})

        return super(NotOnWaitingListMixin, self).dispatch(request, args, kwargs)


class ConHasSpaceOrAlreadyRegisteredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        entries = Registration.objects.order_by('registration_date')
        if len(entries) >= get_con_value('max_attendees'):
            try:
                if is_on_wait_list(entries, request):
                    return render(request, 'con/game_submission_wait_list.html',
                                  {"is_registration_open": is_registration_open()})
            except ValueError:
                return render(request, 'con/game_submission_con_full.html',
                              {"is_registration_open": is_registration_open()})

        return super(ConHasSpaceOrAlreadyRegisteredMixin, self).dispatch(request, args, kwargs)


class RevisionMixin(object):
    orig_dict = {}
    changed = []
    revision_log_prefix = "Source Not Specified"
    changed_ignore_list = []

    def form_valid(self, form):
        changed = []
        for k, v in self.object.__dict__.iteritems():
            if k.startswith("_") or k in self.changed_ignore_list:
                continue

            if self.orig_dict.get(k) != v:
                changed.append(k)

        changed.sort()

        with reversion.create_revision():
            reversion.set_user(self.request.user)
            reversion.set_comment("Form Submission - %s Changed" % ", ".join(changed))

            return super(RevisionMixin, self).form_valid(form)

    def get_object(self, queryset=None):
        result = super(RevisionMixin, self).get_object(queryset)
        self.orig_dict.update(result.__dict__)
        return result

