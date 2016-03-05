from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import render

from ..utils import registration_open


class RegistrationOpenMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not registration_open():
            return render(request, 'con/registration_not_open.html', {})
        return super(RegistrationOpenMixin, self).dispatch(request, args, kwargs)
