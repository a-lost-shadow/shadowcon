from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from shadowcon.tests.utils import SectionCheckMixIn

import json
import os

from .models import Page, Tag


class PageTest(SectionCheckMixIn, TestCase):
    fixtures = ['auth', 'initial']
    url = '/'

    def setUp(self):
        self.client = Client()
        with open(os.path.dirname(os.path.realpath(__file__)) + "/fixtures/initial.json") as json_file:
            self.initial = json.load(json_file)

        Page(name="Tag test", url="tag_test", content="{{a}} {{b}} {{c}}").save()

    def run_initial_test(self, url, name, expected_title=None):
        data = None
        for entry in self.initial:
            try:
                if name == entry['fields']['name']:
                    data = entry['fields']['content']
                    break
            except KeyError:
                pass

        self.assertIsNotNone(data, "Couldn't find '%s' in initial data" % name)

        if not expected_title:
            expected_title = "ShadowCon 2016 - %s" % name

        response = self.client.get(url)

        section = self.get_section(response, 'section id="main" role="main"', '/section')
        self.assertGreater(section.find(data), -1, "Couldn't find initial data for %s in response" % name)
        self.assertSectionContains(response, expected_title, 'title')

    def test_home_as_index(self):
        self.run_initial_test('/', "Home", "ShadowCon 2016")

    def test_home(self):
        self.run_initial_test(reverse("page:display", args=["home"]), "Home", "ShadowCon 2016")

    def test_site_amenities(self):
        self.run_initial_test(reverse("page:display", args=["site_amenities"]), "Site Amenities")

    def test_site_amenities_slash(self):
        self.run_initial_test(reverse("page:display", args=["site/amenities"]), "Site Amenities")

    def test_site_rules(self):
        self.run_initial_test(reverse("page:display", args=["site_rules"]), "Site Rules")

    def test_site_rules_slash(self):
        self.run_initial_test(reverse("page:display", args=["site/rules"]), "Site Rules")

    def run_tag_test(self, expected):
        response = self.client.get(reverse("page:display", args=["tag_test"]))
        section = self.get_section(response, 'section id="main" role="main"', '/section')[31:].strip()
        self.assertEquals(section, expected)

    def test_no_tags(self):
        for entry in Tag.objects.all():
            entry.delete()
        self.run_tag_test("{{a}} {{b}} {{c}}")

    def test_a_tag(self):
        Tag(tag="a", content="123").save()
        self.run_tag_test("123 {{b}} {{c}}")

    def test_b_tag(self):
        Tag(tag="b", content="123").save()
        self.run_tag_test("{{a}} 123 {{c}}")

    def test_c_tag(self):
        Tag(tag="c", content="123").save()
        self.run_tag_test("{{a}} {{b}} 123")

    def test_a_b_tags(self):
        Tag(tag="a", content="123").save()
        Tag(tag="b", content="456").save()
        self.run_tag_test("123 456 {{c}}")

    def test_a_c_tags(self):
        Tag(tag="a", content="123").save()
        Tag(tag="c", content="789").save()
        self.run_tag_test("123 {{b}} 789")

    def test_b_c_tags(self):
        Tag(tag="b", content="456").save()
        Tag(tag="c", content="789").save()
        self.run_tag_test("{{a}} 456 789")

    def test_a_b_c_tags(self):
        Tag(tag="a", content="123").save()
        Tag(tag="b", content="456").save()
        Tag(tag="c", content="789").save()
        self.run_tag_test("123 456 789")

    def test_nonexistent(self):
        response = self.client.get(reverse("page:display", args=["does_not_exist"]))
        self.assertEquals(response.status_code, 404)
