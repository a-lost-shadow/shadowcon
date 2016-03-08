from django.forms import Form, CharField, EmailField, ModelChoiceField, Textarea
from django.utils.html import strip_tags
from .models import ContactReason
from .utils import mail_list


class ContactForm(Form):
    name = CharField(label="Name", max_length=128,)
    email = EmailField(label="E-mail", max_length=128)
    reason = ModelChoiceField(label="Reason", queryset=ContactReason.objects.all())
    summary = CharField(label="Summary", max_length=128)
    message = CharField(label="Message", max_length=5000, widget=Textarea)

    def send_email(self):
        reason = self.cleaned_data.get('reason')
        email_list = reason.list
        subject_source = reason
        subject_details = strip_tags(self.cleaned_data.get('summary'))

        message = strip_tags(self.cleaned_data.get('message'))
        sender = strip_tags(self.cleaned_data.get('email'))

        mail_list(subject_source, subject_details, message, sender, email_list)
