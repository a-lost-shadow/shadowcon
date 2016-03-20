from django.core import mail
from django.test import TestCase
import ddt
import re


class ShadowConTestCase(TestCase):
    fixtures = ['auth', 'initial', 'games']

    def get_section(self, response, section, section_terminator=None):
        if section_terminator is None:
            section_terminator = "/" + section

        section = "<%s>" % section
        section_terminator = "<%s>" % section_terminator

        return self.extract_between(str(response), section, section_terminator)

    def extract_between(self, string, section, section_terminator):
        try:
            start = string.index(section)
            stop = string.index(section_terminator, start) + len(section_terminator)
        except ValueError:
            self.fail("Couldn't find subsection defined by '%s' & '%s' in %s" %
                      (section, section_terminator, string))

        return string[start:stop]

    def assertSectionContains(self, response, pattern, section, section_terminator=None, expected=True):
        self.assertEqual(response.status_code, 200)
        self.assertStringContains(response, pattern, section, section_terminator, expected)

    def assertStringContains(self, string, pattern, section, section_terminator=None, expected=True):
        if section_terminator is None:
            section_terminator = "/" + section

        sub_str = self.get_section(string, section, section_terminator)
        fail_msg = "to find '%s' between %s and %s\n%s" % (pattern, section, section_terminator, sub_str)

        if expected:
            self.assertIsNotNone(re.search(pattern, sub_str), "Expected %s" % fail_msg)
        else:
            self.assertIsNone(re.search(pattern, sub_str), "Didn't expect %s" % fail_msg)

    def get_email(self):
        self.assertEquals(len(mail.outbox), 1)
        return mail.outbox[0]

    def assertEmail(self, to, from_email, body, subject_source=None, subject_details=None, subject=None):
        if subject is None:
            subject = "ShadowCon [%s]: %s" % (subject_source, subject_details)

        email = self.get_email()
        self.assertEquals(email.subject, subject)
        self.assertEquals(email.to, to)
        self.assertEquals(email.from_email, from_email)
        self.assertEquals(email.body, body)


def data_func(*values):
    """
    Method decorator to add to your test methods.
    Should be added to methods of instances of ``unittest.TestCase``.
    """

    def wrapper(func):
        setattr(func, ddt.DATA_ATTR, values[0])
        return func
    return wrapper
