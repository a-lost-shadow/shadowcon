from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from ..models import ConInfo, Game
from ..utils import get_registration
from datetime import date, datetime
from django.template import Context, Template
import pytz
from shadowcon.tests.utils import ShadowConTestCase


def render_template_tag(load, tag, context=Context({})):
    source = "{%% load %s %%}{%% %s %%}" % (load, tag)
    return Template(source).render(context)


def expected_attendance(user):
    result = "\n2016 Registration:\n<ul>\n  \n"
    for reg in get_registration(user):
        result += "  <li>%s</li>\n  \n" % reg
    result += "</ul>\n"
    return result


class TemplateTagsTest(ShadowConTestCase):
    def check_tag(self, load, tag, expected, context=Context({})):
        self.assertEquals(render_template_tag(load, tag, context), expected)

    def test_con_date(self):
        self.check_tag("con_info", "con_date", "April 1st - 3rd, 2016")

    def test_con_date_alternate(self):
        info = ConInfo.objects.all()[0]
        info.date = date(3001, 3, 21)
        info.save()
        self.check_tag("con_info", "con_date", "March 21st - 23rd, 3001")

    def test_con_year(self):
        self.check_tag("con_info", "con_year", "2016")

    def test_con_year_alternate(self):
        info = ConInfo.objects.all()[0]
        info.date = date(4021, 3, 21)
        info.save()
        self.check_tag("con_info", "con_year", "4021")

    def test_con_pre_reg_deadline(self):
        self.check_tag("con_info", "con_pre_reg_deadline", "March 15th, 2016")

    def test_con_pre_reg_deadline_alternate(self):
        info = ConInfo.objects.all()[0]
        info.pre_reg_deadline = date(5432, 6, 8)
        info.save()
        self.check_tag("con_info", "con_pre_reg_deadline", "June 8th, 5432")

    def test_con_game_sub_deadline(self):
        self.check_tag("con_info", "con_game_sub_deadline", "March 22nd, 2016")

    def test_con_game_sub_deadline_alternate(self):
        info = ConInfo.objects.all()[0]
        info.game_sub_deadline = date(1823, 7, 11)
        info.save()
        self.check_tag("con_info", "con_game_sub_deadline", "July 11th, 1823")

    def test_con_game_reg_deadline(self):
        self.check_tag("con_info", "con_game_reg_deadline", "September 15th, 2016<br />6:00:00 PM PDT")

    def test_con_game_reg_deadline_alternate(self):
        info = ConInfo.objects.all()[0]
        info.game_reg_deadline = pytz.timezone("US/Pacific").localize(datetime(1927, 2, 13, 07, 30, 0))
        info.save()
        self.check_tag("con_info", "con_game_reg_deadline", "February 13th, 1927<br />7:30:00 AM PST")

    def test_con_location(self):
        self.check_tag("con_info", "con_location", "Behind the tardis")

    def test_con_location_alternate(self):
        info = ConInfo.objects.all()[0]
        info.location = "DC Universe"
        info.save()
        self.check_tag("con_info", "con_location", "DC Universe")

    def test_con_door_cost(self):
        self.check_tag("con_info", "con_door_cost", "$20.00")

    def test_con__alternate(self):
        info = ConInfo.objects.all()[0]
        info.door_cost = "31.56"
        info.save()
        self.check_tag("con_info", "con_door_cost", "$31.56")

    def test_con_pre_reg_cost(self):
        self.check_tag("con_info", "con_pre_reg_cost", "$10.00")

    def test_con_pre_reg_cost_alternate(self):
        info = ConInfo.objects.all()[0]
        info.pre_reg_cost = 25.82
        info.save()
        self.check_tag("con_info", "con_pre_reg_cost", "$25.82")

    def test_con_registration_opens_before(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = pytz.timezone("US/Pacific").localize(datetime(2037, 6, 3, 22, 27, 42))
        info.save()
        self.check_tag("con_info", "con_registration_opens", "June 3rd, 2037 at 10:27:42 PM PDT")

    def test_con_registration_opens_after(self):
        self.check_tag("con_info", "con_registration_opens", "March 11th, 2015 at 6:38:22 PM PDT")

    def test_con_registration_links_before_no_games_submitted(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = pytz.timezone("US/Pacific").localize(datetime(2037, 6, 3, 22, 27, 42))
        info.save()
        self.check_tag("con_info", "register_links user", """

          <li><a href="/games/register/">Submit Game</a></li>

          <li id="registration_opens"><h3>Registration Opens:</h3>
            <ul><li>June 3rd, 2037<br>10:27:42 PM PDT</li></ul>
          </li>

""")

    def test_con_registration_links_before_games_submitted(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = pytz.timezone("US/Pacific").localize(datetime(2037, 6, 3, 22, 27, 42))
        info.save()
        self.check_tag("con_info", "register_links user", """

          <li><a href="/user/attendance/">Pre-register Attendance</a></li>

          <li><a href="/games/register/">Submit Game</a></li>

          <li id="registration_opens"><h3>Registration Opens:</h3>
            <ul><li>June 3rd, 2037<br>10:27:42 PM PDT</li></ul>
          </li>

""", context=Context({"user": User.objects.get(username="admin")}))

    def test_con_registration_links_after(self):
        self.check_tag("con_info", "register_links user", """

          <li><a href="/user/attendance/">Register Attendance</a></li>

          <li><a href="/games/register/">Submit Game</a></li>

""")

    def test_user_attendance_with_user(self):
        user = User.objects.get(username="user")
        self.check_tag("user", "user_attendance user", expected_attendance(user), context=Context({"user": user}))

    def test_user_attendance_with_staff(self):
        user = User.objects.get(username="staff")
        self.check_tag("user", "user_attendance user", expected_attendance(user), context=Context({"user": user}))

    def test_user_attendance_with_admin(self):
        user = User.objects.get(username="admin")
        self.check_tag("user", "user_attendance user", expected_attendance(user), context=Context({"user": user}))

    def test_user_admin_link_with_user(self):
        user = User.objects.get(username="user")
        self.check_tag("user", "admin_link user", "", context=Context({"user": user}))

    def test_user_admin_link_with_staff(self):
        user = User.objects.get(username="staff")
        expected = '<li><a href="%s">Admin</a></li>' % reverse('admin:index')
        self.check_tag("user", "admin_link user", expected, context=Context({"user": user}))

    def test_user_admin_link_with_admin(self):
        user = User.objects.get(username="admin")
        expected = '<li><a href="%s">Admin</a></li>' % reverse('admin:index')
        self.check_tag("user", "admin_link user", expected, context=Context({"user": user}))

    def test_user_edit_schedule_link_with_user(self):
        user = User.objects.get(username="user")
        self.check_tag("user", "edit_schedule_link user", "", context=Context({"user": user}))

    def test_user_edit_schedule_link_with_staff(self):
        user = User.objects.get(username="staff")
        expected = '<li><a href="%s">Change Schedule</a></li>' % reverse('convention:edit_schedule')
        self.check_tag("user", "edit_schedule_link user", expected, context=Context({"user": user}))

    def test_user_edit_schedule_link_with_admin(self):
        user = User.objects.get(username="admin")
        expected = '<li><a href="%s">Change Schedule</a></li>' % reverse('convention:edit_schedule')
        self.check_tag("user", "edit_schedule_link user", expected, context=Context({"user": user}))

    def test_user_attendance_list_link_with_user(self):
        user = User.objects.get(username="user")
        self.check_tag("user", "attendance_list_link user", "", context=Context({"user": user}))

    def test_user_attendance_list_link_with_staff(self):
        user = User.objects.get(username="staff")
        expected = '<li><a href="%s">View Attendance</a></li>' % reverse('convention:attendance_list')
        self.check_tag("user", "attendance_list_link user", expected, context=Context({"user": user}))

    def test_user_attendance_list_link_with_admin(self):
        user = User.objects.get(username="admin")
        expected = '<li><a href="%s">View Attendance</a></li>' % reverse('convention:attendance_list')
        self.check_tag("user", "attendance_list_link user", expected, context=Context({"user": user}))

    def run_submitted_game_test(self, user):
        response = render_template_tag("games", "show_user_games user", context=Context({"user": user}))

        self.assertTrue(response.startswith('<h3>Submitted Games</h3>\n<div id="accordion">'))
        for game in Game.objects.filter(user=user):
            section = self.get_section(response, 'h3 id="%s"' % game.header_target(), "/div")
            self.assertStringContains(section, game.title, 'h3 id="%s"' % game.header_target(), "/h3")
            self.assertStringContains(section, "<b>%s:</b> %s<br />" % ("Players", game.number_players), 'div')
            self.assertStringContains(section, "<b>%s:</b> %s<br />" % ("System", game.system), 'div')
            self.assertStringContains(section, "<b>%s:</b> %s<br />" % ("Potential Triggers", game.triggers), 'div')
            self.assertStringContains(section, "<b>%s:</b><br>\\s+%s" % ("Description", game.description), 'div')
            self.assertStringContains(section, '<a href="%s">Edit</a>' % reverse("convention:edit_game",
                                                                                 args=(game.id,)),
                                      'div')

    def test_submitted_games_with_games(self):
        self.run_submitted_game_test(User.objects.get(username="admin"))

    def test_submitted_games_no_games(self):
        user = User(username="new_user")
        user.save()
        self.run_submitted_game_test(user)

    def test_game_registration_link_with_registration(self):
        user = User.objects.get(username="admin")
        expected = '<li><a href="https://goo.gl/forms/xKWoC8boOUIFi32U2">Game Registration</a></li>'
        self.check_tag("user", "game_registration_link user", expected, context=Context({"user": user}))

    def test_game_registration_link_with_no_registration(self):
        user = User(username="new_user")
        user.save()
        expected = ''
        self.check_tag("user", "game_registration_link user", expected, context=Context({"user": user}))
