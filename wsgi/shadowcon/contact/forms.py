from django.forms import Form, CharField, EmailField, ModelChoiceField, Textarea
from django.utils.html import strip_tags
from django.core.mail import send_mail
from .models import ContactReason, GroupEmailEntry, UserEmailEntry


class ContactForm(Form):
    name = CharField(label="Name", max_length=128,)
    email = EmailField(label="E-mail", max_length=128)
    reason = ModelChoiceField(label="Reason", queryset=ContactReason.objects.all())
    summary = CharField(label="Summary", max_length=128)
    message = CharField(label="Message", max_length=5000, widget=Textarea)

    def send_email(self):
        reason = self.cleaned_data.get('reason')
        users = map(lambda x: x.user, UserEmailEntry.objects.filter(list=reason.list))
        groups = map(lambda x: x.group, GroupEmailEntry.objects.filter(list=reason.list))
        for group in groups:
            users.extend(group.user_set.all())

        # filter out any duplicate e-mails due to users showing up multiple times in the list
        emails = set(map(lambda x: x.email, users))

        subject = "ShadowCon [%s]: %s" % (reason, strip_tags(self.cleaned_data.get('summary')))
        message = strip_tags(self.cleaned_data.get('message'))
        sender = strip_tags(self.cleaned_data.get('email'))

        send_mail(subject, message, sender, emails)