from ddt import ddt, data
from django.core.urlresolvers import reverse
from django.test import Client
from reversion import revisions as reversion
from reversion_compare.admin import CompareVersionAdmin
from shadowcon.tests.utils import ShadowConTestCase

import json
import os

from .admin import PageAdmin, TagAdmin
from .models import Page, Tag


class PageTest(ShadowConTestCase):
    url = '/'

    def setUp(self):
        self.client = Client()
        with open(os.path.dirname(os.path.realpath(__file__)) + "/fixtures/initial.json") as json_file:
            self.initial = json.load(json_file)

        Page(name="Tag test", url="tag_test", content="{{a}} {{b}} {{c}}").save()

    def run_initial_test(self, url, name, expected_title=None):
        data = None
        for entry in self.initial:
            if name == entry['fields']['name']:
                data = entry['fields']['content']
                break

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
        section = self.get_section(response, 'section id="main" role="main"', '/section')[31:-10].strip()
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

    def test_page_string(self):
        self.assertEquals(str(Page.objects.get(name="Tag test")), "Tag test")

    def test_tag_string(self):
        self.assertEquals(str(Tag(tag="a-123", content="123")), "a-123")


@ddt
class AdminVersionTest(ShadowConTestCase):
    @data(PageAdmin, TagAdmin)
    def test_has_versions(self, clazz):
        self.assertTrue(CompareVersionAdmin.__subclasscheck__(clazz))

    def test_page_versions(self):
        self.client.login(username="admin", password="123")
        page = Page(name="Test Name", url="test-url", content="Content goes here")
        with reversion.create_revision():
            reversion.set_comment("initial")
            page.save()

        versions = reversion.get_for_object(page)
        self.assertEquals(len(versions), 1)
        self.assertEquals(versions[0].revision.comment, "initial")

        url = reverse("admin:page_page_change", args=[page.id])
        self.client.post(url, {"name": "2nd name", "url": "test-url", "content": "New content"})
        page = Page.objects.get(id=page.id)

        self.assertEquals(page.name, "2nd name")
        self.assertEquals(page.content, "New content")

        versions = map(lambda x: x, reversion.get_for_object(page))
        self.assertEquals(len(versions), 2)
        self.assertEquals(versions[0].revision.comment, "Changed name and content.")

        actual_initial = json.loads(versions[1].serialized_data)[0]
        self.assertEquals(actual_initial["fields"]["name"], "Test Name")
        self.assertEquals(actual_initial["fields"]["url"], "test-url")
        self.assertEquals(actual_initial["fields"]["content"], "Content goes here")

        actual_final = json.loads(versions[0].serialized_data)[0]
        self.assertEquals(actual_final["fields"]["name"], "2nd name")
        self.assertEquals(actual_final["fields"]["url"], "test-url")
        self.assertEquals(actual_final["fields"]["content"], "New content")
