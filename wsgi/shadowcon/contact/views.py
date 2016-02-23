from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.core.urlresolvers import reverse
from .forms import ContactForm


class ContactView(FormView):
    template_name = 'contact/contact.html'
    form_class = ContactForm

    def get_success_url(self):
        return reverse('contact:thanks')

    def form_valid(self, form):
        form.send_email()
        return super(ContactView, self).form_valid(form)


class ThanksView(TemplateView):
    template_name = 'contact/thanks.html'
