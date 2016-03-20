from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client
from django.utils.html import escape
from django.utils import timezone
from con.models import Game, TimeBlock, TimeSlot, Location
from shadowcon.tests.utils import ShadowConTestCase, data_func
from ddt import ddt
import os
import json


def get_games():
    with open(os.path.dirname(os.path.realpath(__file__)) + "/../../fixtures/games.json") as f:
        data = json.load(f)

    game_data = filter(lambda x: "con.game" == x["model"], data)
    return map(lambda x: int(x["pk"]), game_data)


def modify_game(game):
    game.title = "Unit Test Title"
    game.gm = "Unit Test GM"
    game.duration = "Unit Test Duration"
    game.number_players = "Unit Test Player Count"
    game.system = "Unit Test System"
    game.triggers = "Unit Test Triggers"
    game.description = "<b>Unit Test Description</b>"
    game.time_block = TimeBlock.objects.all()[0]
    game.time_slot = TimeSlot.objects.all()[0]
    game.location = Location.objects.all()[0]


def check_game(test_class, actual, modified_date):
    test_class.assertEquals(actual.title, "Unit Test Title")
    test_class.assertEquals(actual.gm, "Unit Test GM")
    test_class.assertEquals(actual.duration, "Unit Test Duration")
    test_class.assertEquals(actual.number_players, "Unit Test Player Count")
    test_class.assertEquals(actual.system, "Unit Test System")
    test_class.assertEquals(actual.triggers, "Unit Test Triggers")
    test_class.assertEquals(actual.description, "<b>Unit Test Description</b>")
    test_class.assertGreater(actual.last_modified, modified_date)
    test_class.assertIsNone(actual.last_scheduled)
    test_class.assertIsNone(actual.time_block)
    test_class.assertIsNone(actual.time_slot)
    test_class.assertIsNone(actual.location)


class GameEditTest(ShadowConTestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.client = Client()

    def test_cannot_modify_other_games_get(self):
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('con:edit_game', args=[game.id])

        self.client.login(username='admin', password='123')
        response = self.client.get(url)
        self.assertContains(response, "<h2>Cannot edit another's game</h2>")

    def test_cannot_modify_other_games_post(self):
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('con:edit_game', args=[game.id])

        self.client.login(username='admin', password='123')
        original_title = game.title
        game.title = 'Changed Via Unit Test'

        response = self.client.post(url, game.__dict__)
        self.assertEqual(original_title, Game.objects.get(id=game.id).title)
        self.assertContains(response, "<h2>Cannot edit another's game</h2>")

    def test_modify_without_login_redirects_get(self):
        game = Game.objects.all()[0]
        url = reverse('con:edit_game', args=[game.id])
        login_url = reverse('login')

        response = self.client.get(url)
        self.assertRedirects(response, login_url + "?next=" + url)

    def test_modify_without_login_redirects_post(self):
        game = Game.objects.all()[0]
        url = reverse('con:edit_game', args=[game.id])
        login_url = reverse('login')

        response = self.client.post(url, game.__dict__)
        self.assertRedirects(response, login_url + "?next=" + url)

    def test_can_modify_own_game_get(self):
        self.client.login(username='staff', password='123')
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('con:edit_game', args=[game.id])

        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'value="%s"' % game.title, 'label for="id_title"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.gm, 'label for="id_gm"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.duration, 'label for="id_duration"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.number_players, 'label for="id_number_players"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.system, 'label for="id_system"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.triggers, 'label for="id_triggers"', '/p')
        desc = self.extract_between(self.get_section(response, 'label for="id_description"', '/p'),
                                    'ckeditortype">', '</textarea>')[14:-11]
        self.assertEquals(desc, escape(game.description))

    def test_can_modify_own_game_post(self):
        self.client.login(username='staff', password='123')
        user = User.objects.get(username='staff')
        modified_game = Game.objects.filter(user=user)[0]
        modified_game.time_block = None
        modified_game.time_slot = None
        modified_game.location = None
        modified_game.save()

        modify_game(modified_game)
        modified_date = timezone.now()

        url = reverse('con:edit_game', args=[modified_game.id])
        response = self.client.post(url, modified_game.__dict__)
        self.assertRedirects(response, reverse("con:user_profile"))

        check_game(self, Game.objects.get(id=modified_game.id), modified_date)


class NewGameTest(ShadowConTestCase):
    url = reverse('con:submit_game')
    login_url = reverse('login') + "?next=" + url

    def setUp(self):
        # Every test needs access to the request factory.
        self.client = Client()

    def test_create_without_login_redirects_get(self):

        response = self.client.get(self.url)
        self.assertRedirects(response, self.login_url)

    def test_create_without_login_redirects_post(self):
        game = Game.objects.all()[0]
        response = self.client.post(self.url, game.__dict__)
        self.assertRedirects(response, self.login_url)

    def test_create_logged_in_get(self):
        self.client.login(username='staff', password='123')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'value=', 'label for="id_title"', '/p', False)
        self.assertSectionContains(response, 'value="staff"', 'label for="id_gm"', '/p')
        self.assertSectionContains(response, 'value=', 'label for="id_duration"', '/p', False)
        self.assertSectionContains(response, 'value=', 'label for="id_number_players"', '/p', False)
        self.assertSectionContains(response, 'value=', 'label for="id_system"', '/p', False)
        self.assertSectionContains(response, 'value=', 'label for="id_triggers"', '/p', False)
        desc = self.extract_between(self.get_section(response, 'label for="id_description"', '/p'),
                                    'ckeditortype">', '</textarea>')[14:-11]
        self.assertEquals(desc, "")

    def test_create_logged_in_post(self):
        self.client.login(username='staff', password='123')
        game = Game()
        modify_game(game)
        modified_date = timezone.now()

        response = self.client.post(self.url, game.__dict__)
        self.assertRedirects(response, reverse("con:user_profile"))

        actual = Game.objects.get(title="Unit Test Title")

        check_game(self, actual, modified_date)
        self.assertEquals(actual.user, User.objects.get(username="staff"))

    def test_create_email(self):
        self.client.login(username='staff', password='123')
        game = Game()
        modify_game(game)

        self.client.post(self.url, game.__dict__)
        game = Game.objects.get(title=game.title)
        self.assertEmail(['admin@na.com'], "no-reply@shadowcon.net", game.email_format(None),
                         "Game Submission", "staff submitted '%s'" % game.title)


@ddt
class GameListTest(ShadowConTestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.client = Client()
        self.response = self.client.get(reverse('con:games_list'))

    def test_game_list_title(self):
        self.assertSectionContains(self.response, "ShadowCon 2016 - Game Descriptions", "title")

    def test_game_list_list_header(self):
        self.assertSectionContains(self.response, "2016 Games", "h2")

    @data_func(get_games())
    def test_game_list_game_entries(self, game_id):
        game = Game.objects.get(id=game_id)
        section = self.get_section(self.response, 'div id="%s"' % game.header_target(), '/div')
        self.assertStringContains(section, game.title, "h3")
        self.assertStringContains(section, "GM: %s<br />" % game.gm, "p")
        self.assertStringContains(section, "Time Slot: %s<br />" % game.combined_time(), "p")
        self.assertStringContains(section, "Players: %s<br />" % game.number_players, "p")
        self.assertStringContains(section, "System: %s<br />" % game.system, "p")
        self.assertStringContains(section, "Potential Triggers: %s<br />" % game.triggers, "p")
        self.assertStringContains(section, "Description:<br />\\s+%s<br />" % game.description,
                                  'div id="%s"' % game.header_target(), '/div')
