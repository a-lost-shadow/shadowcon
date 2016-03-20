import ddt
import re


class SectionCheckMixIn(object):
    def get_section(self, response, section, section_terminator=None):
        if section_terminator is None:
            section_terminator = "/" + section

        section = "<%s>" % section
        section_terminator = "<%s>" % section_terminator

        response_str = str(response)
        try:
            start = response_str.index(section)
            stop = response_str.index(section_terminator, start) + len(section_terminator)
        except ValueError:
            self.fail("Couldn't find subsection defined by '%s' & '%s' in %s" %
                      (section, section_terminator, response_str))

        return response_str[start:stop]

    def assertSectionContains(self, response, pattern, section, section_terminator=None, expected=True):
        self.assertEqual(response.status_code, 200)
        self.assertStringContains(response, pattern, section, section_terminator, expected)

    def assertStringContains(self, string, pattern, section, section_terminator=None, expected=True):
        sub_str = self.get_section(string, section, section_terminator)
        fail_msg = "to find '%s' between %s and %s\n%s" % (pattern, section, section_terminator, sub_str)

        if expected:
            self.assertIsNotNone(re.search(pattern, sub_str), "Expected %s" % fail_msg)
        else:
            self.assertIsNone(re.search(pattern, sub_str), "Didn't expect %s" % fail_msg)


def data_func(*values):
    """
    Method decorator to add to your test methods.
    Should be added to methods of instances of ``unittest.TestCase``.
    """

    def wrapper(func):
        setattr(func, ddt.DATA_ATTR, values[0])
        return func
    return wrapper
