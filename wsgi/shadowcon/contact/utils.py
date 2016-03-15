from django.core.mail import send_mail

from .models import EmailList, UserEmailEntry, GroupEmailEntry


def mail_list(subject_source, subject_details, message, sender, email_list=None, list_name=None):
    if email_list is None:
        if list_name is None:
            raise ValueError("Both email_list and list_name are None")
        email_list = EmailList.objects.get(name=list_name)

    users = map(lambda x: x.user, UserEmailEntry.objects.filter(list=email_list))
    groups = map(lambda x: x.group, GroupEmailEntry.objects.filter(list=email_list))
    for group in groups:
        users.extend(group.user_set.all())

    # filter out any duplicate e-mails due to users showing up multiple times in the list
    emails = set(map(lambda x: x.email, users))

    subject = "ShadowCon [%s]: %s" % (subject_source, subject_details)

    send_mail(subject, message, sender, emails)
