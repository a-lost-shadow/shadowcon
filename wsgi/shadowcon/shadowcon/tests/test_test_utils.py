from .utils import ShadowConTestCase


class Tests(ShadowConTestCase):
    data = "<a><b>Test Data</b></a>"

    def test_outer_section_parsing(self):
        self.assertEquals(self.get_section(self.data, 'a'), '<a><b>Test Data</b></a>')

    def test_inner_section_parsing(self):
        self.assertEquals(self.get_section(self.data, 'b'), '<b>Test Data</b>')

    def test_custom_section_parsing(self):
        self.assertEquals(self.get_section(self.data, 'b', '/a'), '<b>Test Data</b></a>')

    def test_invalid_section_start(self):
        with self.assertRaises(AssertionError) as e:
            self.get_section(self.data, 'c', '/a')
        self.assertEquals(e.exception.message,
                          "Couldn't find subsection defined by '<c>' & '</a>' in <a><b>Test Data</b></a>")

    def test_invalid_section_stop(self):
        with self.assertRaises(AssertionError) as e:
            self.get_section(self.data, 'a', '/c')
        self.assertEquals(e.exception.message,
                          "Couldn't find subsection defined by '<a>' & '</c>' in <a><b>Test Data</b></a>")

    def test_invalid_section_start_and_stop(self):
        with self.assertRaises(AssertionError) as e:
            self.get_section(self.data, 'c', '/c')
        self.assertEquals(e.exception.message,
                          "Couldn't find subsection defined by '<c>' & '</c>' in <a><b>Test Data</b></a>")
