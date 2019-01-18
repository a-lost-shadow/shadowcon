from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client
from django.test.utils import override_settings
from django.utils.html import escape
from django.utils import timezone
from convention.models import Game, TimeBlock, TimeSlot, Location, ConInfo, Registration
from convention.utils import friendly_username
from convention.views.games import get_block_offset, get_start, get_width, get_index
from shadowcon.tests.utils import ShadowConTestCase, data_func
from ddt import ddt, data, unpack
from datetime import timedelta
from reversion import revisions as reversion
import os
import json


def get_games():
    with open(os.path.dirname(os.path.realpath(__file__)) + "/../../fixtures/games.json") as f:
        json_data = json.load(f)

    game_data = filter(lambda x: "convention.game" == x["model"], json_data)
    return map(lambda x: int(x["pk"]), game_data)


def modify_game(game):
    game.title = "Unit Test Title"
    game.gm = "Unit Test GM"
    game.game_length = "Unit Test Game Length"
    game.number_players = "Unit Test Player Count"
    game.system = "Unit Test System"
    game.triggers = "Unit Test Triggers"
    game.description = "<b>Unit Test Description</b>"
    game.preferred_time = "Unit Test Preferred Time"
    game.special_requests = "Unit Test Special Request"
    game.time_block = TimeBlock.objects.all()[0]
    game.time_slot = TimeSlot.objects.all()[0]
    game.location = Location.objects.all()[0]
    game.convention = ConInfo.objects.all()[0]


def check_game(test_class, actual, modified_date):
    test_class.assertEquals(actual.title, "Unit Test Title")
    test_class.assertEquals(actual.gm, "Unit Test GM")
    test_class.assertEquals(actual.game_length, "Unit Test Game Length")
    test_class.assertEquals(actual.number_players, "Unit Test Player Count")
    test_class.assertEquals(actual.system, "Unit Test System")
    test_class.assertEquals(actual.triggers, "Unit Test Triggers")
    test_class.assertEquals(actual.description, "<b>Unit Test Description</b>")
    test_class.assertEquals(actual.preferred_time, "Unit Test Preferred Time")
    test_class.assertEquals(actual.special_requests, "Unit Test Special Request")
    test_class.assertGreater(actual.last_modified, modified_date)
    test_class.assertIsNone(actual.last_scheduled)
    test_class.assertIsNone(actual.time_block)
    test_class.assertIsNone(actual.time_slot)
    test_class.assertIsNone(actual.location)


@ddt
class GameEditTest(ShadowConTestCase):
    def setUp(self):
        self.client = Client()

    def test_cannot_modify_other_games_get(self):
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('convention:edit_game', args=[game.id])

        self.client.login(username='admin', password='123')
        response = self.client.get(url)
        self.assertContains(response, "<h2>Cannot edit another's game</h2>")

    def test_cannot_modify_other_games_post(self):
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('convention:edit_game', args=[game.id])

        self.client.login(username='admin', password='123')
        original_title = game.title
        game.title = 'Changed Via Unit Test'

        response = self.client.post(url, game.__dict__)
        self.assertEqual(original_title, Game.objects.get(id=game.id).title)
        self.assertContains(response, "<h2>Cannot edit another's game</h2>")

    def test_modify_without_login_redirects_get(self):
        game = Game.objects.all()[0]
        url = reverse('convention:edit_game', args=[game.id])
        login_url = reverse('login')

        response = self.client.get(url)
        self.assertRedirects(response, login_url + "?next=" + url)

    def test_modify_without_login_redirects_post(self):
        game = Game.objects.all()[0]
        url = reverse('convention:edit_game', args=[game.id])
        login_url = reverse('login')

        response = self.client.post(url, game.__dict__)
        self.assertRedirects(response, login_url + "?next=" + url)

    def test_can_modify_own_game_get(self):
        self.client.login(username='staff', password='123')
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('convention:edit_game', args=[game.id])

        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'value="%s"' % game.title, 'label for="id_title"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.gm, 'label for="id_gm"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.game_length, 'label for="id_game_length"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.number_players, 'label for="id_number_players"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.system, 'label for="id_system"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.triggers, 'label for="id_triggers"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.preferred_time, 'label for="id_preferred_time"', '/p')
        self.assertSectionContains(response, 'value="%s"' % game.special_requests, 'label for="id_special_requests"', '/p')
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

        url = reverse('convention:edit_game', args=[modified_game.id])
        response = self.client.post(url, modified_game.__dict__)
        self.assertRedirects(response, reverse("convention:user_profile"))

        check_game(self, Game.objects.get(id=modified_game.id), modified_date)

    @data(("", {}),
          ("title", {"title": "New Title"}),
          ("gm", {"gm": "New GM"}),
          ("gm, title", {"gm": "New GM", "title": "New Title"}),
          ("description, gm, title", {"gm": "New GM", "title": "New Title", "description": "<b>HA!</b>"}),
          )
    @unpack
    def test_modify_revision(self, expected, updates):
        self.client.login(username='staff', password='123')
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]

        post = game.__dict__
        post.update(updates)

        url = reverse('convention:edit_game', args=[game.id])
        self.client.post(url, game.__dict__)

        versions = map(lambda x: x, reversion.get_for_object(game))

        self.assertEquals(len(versions), 1)
        self.assertEquals(versions[0].revision.comment, "Form Submission - %s Changed" % expected)

    def test_modify_before_con_open_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.save()
        self.test_can_modify_own_game_get()

    def test_modify_after_con_open_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.save()
        self.test_can_modify_own_game_get()

    def test_modify_before_con_open_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.save()
        self.test_can_modify_own_game_post()

    def test_modify_after_con_open_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.save()
        self.test_can_modify_own_game_post()

    def test_triggers_shown(self):
        self.client.login(username='staff', password='123')
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('convention:edit_game', args=[game.id])

        response = self.client.get(url)
        self.assertSectionContains(response, '<h3>Example Triggers</h3>', 'h3', '/ul')
        self.assertSectionContains(response, '<li>Food</li>', 'h3', '/ul')
        self.assertSectionContains(response, '<li>Spiders</li>', 'h3', '/ul')
        self.assertSectionContains(response, '<li>Kittens</li>', 'h3', '/ul')


class NewGameTest(ShadowConTestCase):
    url = reverse('convention:submit_game')
    login_url = reverse('login') + "?next=" + url

    def setUp(self):
        self.client = Client()

    def test_create_without_login_redirects_get(self):

        response = self.client.get(self.url)
        self.assertRedirects(response, self.login_url)

    def test_create_without_login_redirects_post(self):
        game = Game.objects.all()[0]
        response = self.client.post(self.url, game.__dict__)
        self.assertRedirects(response, self.login_url)

    def run_create_get_test(self, username):
        self.client.login(username=username, password='123')
        expected_username = friendly_username(User.objects.get(username=username))

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'value=', 'label for="id_title"', '/p', False)
        self.assertSectionContains(response, 'value="%s"' % expected_username, 'label for="id_gm"', '/p')
        self.assertSectionContains(response, 'value=', 'label for="id_game_length"', '/p', False)
        self.assertSectionContains(response, 'value=', 'label for="id_number_players"', '/p', False)
        self.assertSectionContains(response, 'value=', 'label for="id_system"', '/p', False)
        self.assertSectionContains(response, 'value=', 'label for="id_triggers"', '/p', False)
        self.assertSectionContains(response, 'value=', 'label for="id_preferred_time"', '/p', False)
        self.assertSectionContains(response, 'value=', 'label for="id_special_requests"', '/p', False)
        desc = self.extract_between(self.get_section(response, 'label for="id_description"', '/p'),
                                    'ckeditortype">', '</textarea>')[14:-11]
        self.assertEquals(desc, "")

    def test_create_logged_in_get(self):
        self.run_create_get_test('staff')

    def test_create_before_con_open_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.save()
        self.run_create_get_test('staff')

    def test_create_before_con_open_new_user_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.save()
        user = User(username='new-user')
        user.set_password('123')
        user.save()
        self.run_create_get_test('new-user')

    def test_create_before_con_open_con_full_registered_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.max_attendees = len(Registration.objects.all())
        info.save()
        self.run_create_get_test('admin')

    def test_create_before_con_open_con_full_wait_list_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.max_attendees = 0
        info.save()
        self.client.login(username='admin', password='123')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'On Wait List', 'h2')
        self.assertSectionContains(response, 'we cannot accept game submissions from people on the wait ', 'h2', '/p')

    def test_create_before_con_open_con_full_not_registered_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.max_attendees = 0
        info.save()
        user = User(username='new-user')
        user.set_password('123')
        user.save()
        self.client.login(username='new-user', password='123')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'Con Full', 'h2')
        self.assertSectionContains(response, 'a href', 'section id="main" role="main"', '/section', False)
        self.assertSectionContains(response, 'Once registration opens', 'section id="main" role="main"', '/section')

    def test_create_after_con_open_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.save()
        self.run_create_get_test('staff')

    def test_create_after_con_open_new_user_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.save()
        user = User(username='new-user')
        user.set_password('123')
        user.save()
        self.run_create_get_test('new-user')

    def test_create_after_con_open_con_full_registered_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.max_attendees = len(Registration.objects.all())
        info.save()
        self.run_create_get_test('admin')

    def test_create_after_con_open_con_full_games_wait_list_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.max_attendees = 0
        info.save()
        self.client.login(username='admin', password='123')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'On Wait List', 'h2')
        self.assertSectionContains(response, 'we cannot accept game submissions from people on the wait ', 'h2', '/p')

    def test_create_after_con_open_con_full_not_registered_get(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.max_attendees = 0
        info.save()
        user = User(username='new-user')
        user.set_password('123')
        user.save()
        self.client.login(username='new-user', password='123')

        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'Con Full', 'h2')
        self.assertSectionContains(response, 'a href', 'section id="main" role="main"', '/section')
        self.assertSectionContains(response, 'Once registration opens', 'section id="main" role="main"', '/section',
                                   False)

    def run_create_post_test(self, username):
        self.client.login(username=username, password='123')
        game = Game()
        modify_game(game)
        modified_date = timezone.now()

        response = self.client.post(self.url, game.__dict__)
        self.assertRedirects(response, reverse("convention:user_profile"))

        actual = Game.objects.get(title="Unit Test Title")

        check_game(self, actual, modified_date)
        self.assertEquals(actual.user, User.objects.get(username=username))

    def test_create_logged_in_post(self):
        self.run_create_post_test('staff')

    def test_create_before_con_open_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.save()
        self.run_create_post_test('staff')

    def test_create_before_con_open_new_user_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.save()
        user = User(username='new-user')
        user.set_password('123')
        user.save()
        self.run_create_post_test('new-user')

    def test_create_before_con_open_con_full_registered_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.max_attendees = len(Registration.objects.all())
        info.save()
        self.run_create_post_test('admin')

    def test_create_before_con_open_con_full_wait_list_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.max_attendees = 0
        info.save()
        self.client.login(username='admin', password='123')
        game = Game()
        modify_game(game)

        response = self.client.post(self.url, game.__dict__)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'On Wait List', 'h2')
        self.assertSectionContains(response, 'we cannot accept game submissions from people on the wait ', 'h2', '/p')

    def test_create_before_con_open_con_full_not_registered_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() + timedelta(days=1)
        info.max_attendees = 0
        info.save()
        user = User(username='new-user')
        user.set_password('123')
        user.save()
        self.client.login(username='new-user', password='123')
        game = Game()
        modify_game(game)

        response = self.client.post(self.url, game.__dict__)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'Con Full', 'h2')
        self.assertSectionContains(response, 'a href', 'section id="main" role="main"', '/section', False)
        self.assertSectionContains(response, 'Once registration opens', 'section id="main" role="main"', '/section')

    def test_create_after_con_open_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.save()
        self.run_create_post_test('staff')

    def test_create_after_con_open_new_user_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.save()
        user = User(username='new-user')
        user.set_password('123')
        user.save()
        self.run_create_post_test('new-user')

    def test_create_after_con_open_con_full_registered_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.max_attendees = len(Registration.objects.all())
        info.save()
        self.run_create_post_test('admin')

    def test_create_after_con_open_con_full_wait_list_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.max_attendees = 0
        info.save()
        self.client.login(username='admin', password='123')
        game = Game()
        modify_game(game)

        response = self.client.post(self.url, game.__dict__)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'On Wait List', 'h2')
        self.assertSectionContains(response, 'we cannot accept game submissions from people on the wait ', 'h2', '/p')

    def test_create_after_con_open_con_full_not_registered_post(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now() - timedelta(days=1)
        info.max_attendees = 0
        info.save()
        user = User(username='new-user')
        user.set_password('123')
        user.save()
        self.client.login(username='new-user', password='123')
        game = Game()
        modify_game(game)

        response = self.client.post(self.url, game.__dict__)
        self.assertEquals(response.status_code, 200)
        self.assertSectionContains(response, 'Con Full', 'h2')
        self.assertSectionContains(response, 'a href', 'section id="main" role="main"', '/section')
        self.assertSectionContains(response, 'Once registration opens', 'section id="main" role="main"', '/section',
                                   False)

    def test_create_email(self):
        self.client.login(username='staff', password='123')
        game = Game()
        modify_game(game)

        self.client.post(self.url, game.__dict__)
        game = Game.objects.get(title=game.title)
        self.assertEmail(['admin-test@mg.shadowcon.net'], game.email_format(None), "Game Submission",
                         "staff submitted '%s'" % game.title)

    def test_create_revision(self):
        self.client.login(username='staff', password='123')
        game = Game()
        modify_game(game)

        response = self.client.post(self.url, game.__dict__)
        self.assertRedirects(response, reverse("convention:user_profile"))

        actual = Game.objects.get(title="Unit Test Title")

        versions = reversion.get_for_object(actual)
        self.assertEquals(len(versions), 1)
        self.assertEquals(versions[0].revision.comment, "Form Submission - New")

    def test_triggers_shown(self):
        self.client.login(username='staff', password='123')
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('convention:edit_game', args=[game.id])

        response = self.client.get(url)
        self.assertSectionContains(response, '<h3>Example Triggers</h3>', 'h3', '/ul')
        self.assertSectionContains(response, '<li>Food</li>', 'h3', '/ul')
        self.assertSectionContains(response, '<li>Spiders</li>', 'h3', '/ul')
        self.assertSectionContains(response, '<li>Kittens</li>', 'h3', '/ul')


@ddt
class GameListTest(ShadowConTestCase):
    def setUp(self):
        self.client = Client()
        self.response = self.client.get(reverse('convention:games_list'))

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


@ddt
class GameShowScheduleTest(ShadowConTestCase):
    def setUp(self):
        self.client = Client()
        self.response = self.client.get(reverse('convention:show_schedule'))

    def test_game_list_title(self):
        self.assertSectionContains(self.response, "ShadowCon 2016 - Schedule", "title")

    def test_game_list_list_header(self):
        self.assertSectionContains(self.response, "2016 Schedule", "h2")

    @data_func(get_games())
    def test_game_list_game_entries(self, game_id):
        game = Game.objects.get(id=game_id)
        time_block = game.time_block.text if game.time_block else "Not Scheduled"
        section = self.get_section(self.response, 'table id="%s" class="schedule" border="1"' % time_block, '/table')
        self.assertStringContains(section, time_block, 'th colspan="4" align="left"', "/th")
        pattern = '%s</a></td>\\s+<td>%s</td>\\s+<td>%s</td>\\s+<td>%s</td>' % \
                  (game.title, game.combined_time(), game.number_players, game.gm)
        self.assertStringContains(section, pattern,
                                  'a href="%s#%s"' % (reverse('convention:games_list'), game.header_target()), "/tr")

    def test_javascript_schedule(self):
        self.assertSectionContains(self.response, '<div id="schedule"></div>', 'h2', '/div')

    def test_ajax_hookup(self):
        self.assertSectionContains(self.response, 'registerSchedule\\("#schedule", \'%s\'\\);' %
                                   reverse('convention:ajax_location_schedule_view'), 'head')


@ddt
class GameEditScheduleTest(ShadowConTestCase):
    def setUp(self):
        self.client = Client()
        self.client.login(username='staff', password='123')
        self.url = reverse('convention:edit_schedule')
        self.response = self.client.get(self.url)

    def test_game_list_title(self):
        self.assertSectionContains(self.response, "ShadowCon 2016 - Edit Schedule", "title")

    def test_javascript_schedule(self):
        self.assertSectionContains(self.response, "", 'div id="schedule"', '/div')

    def test_javascript_schedule_table(self):
        pattern = "<tr>\\s+\\s+<th>Game</th>\\s+<th>GM</th>\\s+<th>Preference</th>\\s+<th>Special Requests</th>\\s+" \
                  "<th>Block</th>\\s+<th>Slot</th>\\s+<th>Location</th>\\s+</tr>"
        self.assertSectionContains(self.response, pattern, 'table id="schedule_edit" width="100%" border="1"', '/table')

    def test_ajax_hookup(self):
        self.assertSectionContains(self.response, 'registerSchedule\\("#schedule",\\s+\'%s\',\\s+"#schedule_edit"\\);' %
                                   reverse('convention:ajax_location_schedule_view'), 'head')

    def test_save_button(self):
        pattern = '<span class="glyphicon glyphicon-floppy-disk" aria-hidden="true"></span>&nbsp;Save'
        self.assertSectionContains(self.response, pattern,
                                   'button type="button" class="btn btn-default" id="save" disabled', '/button')

    def test_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('login') + "?next=" + self.url)

    def test_logged_in_user(self):
        self.client.logout()
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Staff Permissions Required", "h2")

    def test_logged_in_staff(self):
        # login credentials inherited
        self.assertSectionContains(self.response, "Edit 2016 Schedule", "h2")

    def test_logged_in_admin(self):
        self.client.logout()
        self.client.login(username="admin", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Edit 2016 Schedule", "h2")


@ddt
class GameScheduleAjaxTest(ShadowConTestCase):
    url = reverse('convention:ajax_location_schedule_view')

    def setUp(self):
        self.client = Client(HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_ajax_schedule_get(self):
        response = self.client.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response._headers["content-type"], ('Content-Type', 'application/json'))

    def test_ajax_schedule_get_locations(self):
        response = self.client.get(self.url)
        json_data = json.loads(response.content)["content"]["locations"]
        items = map(lambda x: {"text": x.text, "id": x.id}, Location.objects.all())
        self.assertEquals(json_data, items)

    def test_ajax_schedule_get_blocks(self):
        response = self.client.get(self.url)
        json_data = json.loads(response.content)["content"]["blocks"]
        items = map(lambda x: {"text": x.text, "id": x.id, "offset": get_block_offset(x)}, TimeBlock.objects.all())
        self.assertEquals(json_data, items)

    def test_ajax_schedule_get_slots(self):
        response = self.client.get(self.url)
        json_data = json.loads(response.content)["content"]["slots"]
        items = map(lambda x: {"text": str(x), "id": x.id, "start": x.start, "width": get_width(x)},
                    TimeSlot.objects.all())
        self.assertEquals(json_data, items)

    def lookup(self, clazz, json_data, index):
        if -1 == index:
            return None
        return clazz.objects.get(id=json_data[index]["id"])

    def test_ajax_schedule_get_games(self):
        response = self.client.get(self.url)
        json_data = json.loads(response.content)["content"]
        for game_data in json_data["games"]:
            game = Game.objects.get(id=game_data["id"])
            self.assertEquals(game.title, game_data["title"])
            self.assertEquals(game.gm, game_data["gm"])
            self.assertEquals(game.location, self.lookup(Location, json_data["locations"], game_data["location"]))
            self.assertEquals(game.time_block, self.lookup(TimeBlock, json_data["blocks"], game_data["time_block"]))
            self.assertEquals(game.time_slot, self.lookup(TimeSlot, json_data["slots"], game_data["time_slot"]))
            self.assertEquals(get_start(game), game_data["start"])
            self.assertEquals(get_width(game.time_slot), game_data["width"])

    @data(("Friday Night", -18), ("Friday MidniGHT", 6), ("Saturday day", 6), ("Saturday midnight", 30),
          ("Sunday Too early", 30), ("Unknown With Words", 100), ("Unknown", 100))
    @unpack
    def test_get_block_offset(self, text, expected):
        block = TimeBlock(text=text, sort_id=0)
        self.assertEquals(get_block_offset(block), expected)

    @data(("Friday Night", 18, 0), ("Friday MidniGHT", 2, 8), ("Saturday day", 10, 16), ("Saturday midnight", 0, 30),
          ("Sunday Too early", 10, 40), ("Unknown With Words", 10, 110), ("Unknown", 20, 120))
    @unpack
    def test_get_start(self, block, start, expected):
        game = Game()
        game.time_block = TimeBlock(text=block, sort_id=0)
        game.time_slot = TimeSlot(start=start, stop=23)
        self.assertEquals(get_start(game), expected)

    def test_get_start_no_block(self):
        game = Game()
        game.time_block = None
        game.time_slot = TimeSlot(start=5, stop=23)
        self.assertEquals(get_start(game), 100)

    def test_get_start_no_slot(self):
        game = Game()
        game.time_block = TimeBlock(text="Friday Night", sort_id=0)
        game.time_slot = None
        self.assertEquals(get_start(game), 100)

    def test_get_start_no_block_no_slot(self):
        game = Game()
        self.assertEquals(get_start(game), 100)

    @data((0, 10, 10), (5, 4, 23), (18.5, 23.75, 5.25), (12, 12, 0))
    @unpack
    def test_get_width(self, start, stop, expected):
        self.assertEquals(get_width(TimeSlot(start=start, stop=stop)), expected)

    def test_get_width_none(self):
        self.assertEquals(get_width(None), 0)

    @data(([1, 2, 3], 1, 0), ([1, 2, 3], 2, 1), ([1, 2, 3], 3, 2), ([1, 2, 3], 4, -1))
    @unpack
    def test_get_index(self, object_list, obj, expected):
        self.assertEquals(get_index(obj, object_list), expected)

    @override_settings(DEBUG=True)
    def test_post_not_logged_in_debug(self):
        response = self.client.post(self.url)
        json_data = json.loads(response.content)

        self.assertEquals(json_data["statusText"], "INTERNAL SERVER ERROR")
        self.assertTrue(json_data["content"].startswith("Exception\nNot logged in!  Only staff have access to this"))
        self.assertEquals(json_data["status"], 500)

    @override_settings(DEBUG=False)
    def test_post_not_logged_in(self):
        response = self.client.post(self.url)
        json_data = json.loads(response.content)

        self.assertEquals(json_data["statusText"], "INTERNAL SERVER ERROR")
        self.assertEquals(json_data["content"], "An error occured while processing an AJAX request.")
        self.assertEquals(json_data["status"], 500)

    @override_settings(DEBUG=True)
    def test_post_not_staff_debug(self):
        self.client.login(username="user", password="123")
        response = self.client.post(self.url)
        json_data = json.loads(response.content)

        self.assertEquals(json_data["statusText"], "INTERNAL SERVER ERROR")
        self.assertTrue(json_data["content"].startswith("Exception\nOnly staff have access to this function"))
        self.assertEquals(json_data["status"], 500)

    @override_settings(DEBUG=False)
    def test_post_not_staff(self):
        self.client.login(username="user", password="123")
        response = self.client.post(self.url)
        json_data = json.loads(response.content)

        self.assertEquals(json_data["statusText"], "INTERNAL SERVER ERROR")
        self.assertEquals(json_data["content"], "An error occured while processing an AJAX request.")
        self.assertEquals(json_data["status"], 500)

    def run_post_test(self, username,
                      location=Location.objects.all()[0],
                      time_block=TimeBlock.objects.all()[0],
                      time_slot=TimeSlot.objects.all()[0]):
        self.client.login(username=username, password="123")

        game = Game()
        modify_game(game)
        game.user = User.objects.get(username=username)
        game.last_modified = timezone.now() - timedelta(days=-1)
        game.save()
        modified_date = timezone.now()

        game = Game.objects.get(title="Unit Test Title")
        post_data = {"id": game.id}
        if location:
            post_data["location"] = location.id
        if time_block:
            post_data["time_block"] = time_block.id
        if time_slot:
            post_data["time_slot"] = time_slot.id
        self.client.post(self.url, post_data)

        game = Game.objects.get(title="Unit Test Title")
        self.assertGreater(game.last_scheduled, modified_date)
        self.assertEquals(game.time_block, time_block)
        self.assertEquals(game.time_slot, time_slot)
        self.assertEquals(game.location, location)

    def test_post_staff(self):
        self.run_post_test("staff")

    def test_post_admin(self):
        self.run_post_test("admin")

    def test_post_no_location(self):
        self.run_post_test("staff", location=None)

    def test_post_no_time_block(self):
        self.run_post_test("staff", time_block=None)

    def test_post_no_time_slot(self):
        self.run_post_test("staff", time_slot=None)

    @data(("", {}),
          ("location", {"location": 2}),
          ("time_block", {"time_block": 2}),
          ("time_slot", {"time_slot": 2}),
          ("location, time_block", {"time_block": 2, "location": 2}),
          ("location, time_slot", {"time_slot": 2, "location": 2}),
          ("location, time_block, time_slot", {"time_slot": 2, "location": 2, "time_block": 2}),
          )
    @unpack
    def test_post_revision(self, expected, updates):
        self.client.login(username="staff", password="123")

        post_data = {"location": 1, "time_block": 1, "time_slot": 1}

        game = Game()
        modify_game(game)
        game.user = User.objects.get(username="staff")
        game.location = Location.objects.get(id=post_data["location"])
        game.time_block = TimeBlock.objects.get(id=post_data["time_block"])
        game.time_slot = TimeSlot.objects.get(id=post_data["time_slot"])
        game.last_modified = timezone.now()
        game.save()

        post_data["id"] = game.id

        self.assertEquals(len(reversion.get_for_object(game)), 0)

        post_data.update(updates)
        self.client.post(self.url, post_data)

        versions = reversion.get_for_object(game)
        self.assertEquals(len(versions), 1)
        self.assertEquals(versions[0].revision.comment, "AJAX Schedule Submission - %s Changed" % expected)
