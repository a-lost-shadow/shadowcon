from django.core.urlresolvers import reverse
from django.test import Client
from django.utils import timezone
from convention.models import ConInfo
from datetime import date, datetime
import pytz
from shadowcon.tests.utils import ShadowConTestCase


class BaseTemplateTest(ShadowConTestCase):
    url = '/'

    def setUp(self):
        self.client = Client()

    def test_header_contains_date(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response, "April 1st - 3rd, 2016", "header")

    def test_header_contains_alternate_date(self):
        info = ConInfo.objects.all()[0]
        info.date = date(2017, 03, 13)
        info.save()
        response = self.client.get(self.url)
        self.assertSectionContains(response, "March 13th - 15th, 2017", "header")

    def test_header_contains_location(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Behind the tardis", "header")

    def test_header_contains_alternate_location(self):
        info = ConInfo.objects.all()[0]
        info.location = "Unit Test Location"
        info.save()
        response = self.client.get(self.url)
        self.assertSectionContains(response, "Unit Test Location", "header")

    # ################################################################
    # ########################## Nav Bar #############################
    # ################################################################

    def test_nav_contains_home(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="/">Home</a></li>', "nav")

    # ########################## Game Menu #############################
    def test_nav_contains_game_menu(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="#">Games</a>\\s+<ul>', "nav")

    def test_game_menu_contains_schedule(self):
        url = reverse('convention:show_schedule')
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Schedule</a></li>' % url, 'a href="#">Games</a', '/ul')

    def test_game_menu_contains_list(self):
        url = reverse('convention:games_list')
        menu_start = 'a href="#">Games</a'
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Description</a></li>' % url, menu_start, '/ul')

    def test_game_menu_contains_submit_game(self):
        url = reverse('convention:submit_game')
        response = self.client.get(self.url)
        menu_start = 'a href="#">Games</a'
        self.assertSectionContains(response, '<li><a href="%s">Submit Game</a></li>' % url, menu_start, '/ul')

    def test_game_menu_contains_submissions(self):
        url = reverse('convention:user_profile')
        response = self.client.get(self.url)
        menu_start = 'a href="#">Games</a'
        self.assertSectionContains(response, '<li><a href="%s">Edit Submissions</a></li>' % url, menu_start, '/ul')

    def test_game_menu_no_schedule_games_without_user(self):
        url = reverse('convention:edit_schedule')
        text = "Change Schedule"
        response = self.client.get(self.url)
        menu_start = 'a href="#">Games</a'
        self.assertSectionContains(response, '<li><a href="%s">%s</a></li>' % (url, text), menu_start, '/ul', False)

    def test_game_menu_no_schedule_games_with_user(self):
        self.client.login(username="user", password="123")
        url = reverse('convention:edit_schedule')
        text = "Change Schedule"
        response = self.client.get(self.url)
        menu_start = 'a href="#">Games</a'
        self.assertSectionContains(response, '<li><a href="%s">%s</a></li>' % (url, text), menu_start, '/ul', False)

    def test_game_menu_schedule_games_with_staff(self):
        self.client.login(username="staff", password="123")
        url = reverse('convention:edit_schedule')
        response = self.client.get(self.url)
        menu_start = 'a href="#">Games</a'
        self.assertSectionContains(response, '<li><a href="%s">Change Schedule</a></li>' % url, menu_start, '/ul')

    def test_game_menu_schedule_games_with_admin(self):
        self.client.login(username="admin", password="123")
        url = reverse('convention:edit_schedule')
        menu_start = 'a href="#">Games</a'
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Change Schedule</a></li>' % url, menu_start, '/ul')

    def test_nav_contains_game_registration_menu_with_registration(self):
        self.client.login(username="admin", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response,
                                   '<li><a href="https://goo.gl/forms/xKWoC8boOUIFi32U2">Game Registration</a></li>',
                                   "nav")

    def test_nav_does_not_contain_game_registration_menu_with_no_user(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response,
                                   '<li><a href="https://goo.gl/forms/xKWoC8boOUIFi32U2">Game Registration</a></li>',
                                   "nav",
                                   expected=False)

    def test_nav_does_not_contain_game_registration_menu_with_no_registration(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response,
                                   '<li><a href="https://goo.gl/forms/xKWoC8boOUIFi32U2">Game Registration</a></li>',
                                   "nav",
                                   expected=False)

    # ########################## Site Menu #############################
    def test_nav_contains_site_menu(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="#">Site</a>\\s+<ul>', "nav")

    def test_site_menu_contains_directions(self):
        url = reverse('page:display', args=["site/directions"])
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Directions</a></li>' % url, 'a href="#">Site</a', '/ul')

    def test_site_menu_contains_rules(self):
        url = reverse('page:display', args=["site/rules"])
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Rules</a></li>' % url, 'a href="#">Site</a', '/ul')

    def test_site_menu_contains_amenities(self):
        url = reverse('page:display', args=["site/amenities"])
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Amenities</a></li>' % url, 'a href="#">Site</a', '/ul')

    # ########################## Account Menu #############################
    def test_nav_contains_login_without_user(self):
        url = reverse('login') + "\\?next=" + self.url
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Login</a></li>' % url, "nav")

    def test_nav_no_login_with_user(self):
        self.client.login(username="user", password="123")
        url = reverse('login') + "\\?next=" + self.url
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Login</a></li>' % url, "nav", expected=False)

    def test_nav_no_login_with_staff(self):
        self.client.login(username="staff", password="123")
        url = reverse('login') + "\\?next=" + self.url
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Login</a></li>' % url, "nav", expected=False)

    def test_nav_no_login_with_admin(self):
        self.client.login(username="admin", password="123")
        url = reverse('login') + "\\?next=" + self.url
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Login</a></li>' % url, "nav", expected=False)

    def test_nav_no_account_menu_without_user(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="#">Account</a>\\s+<ul>', "nav", expected=False)

    def test_nav_contains_account_menu_with_user(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="#">Account</a>\\s+<ul>', "nav")

    def test_nav_contains_account_menu_with_staff(self):
        self.client.login(username="staff", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="#">Account</a>\\s+<ul>', "nav")

    def test_nav_contains_account_menu_with_admin(self):
        self.client.login(username="admin", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="#">Account</a>\\s+<ul>', "nav")

    def test_account_menu_contains_profile_with_user(self):
        self.client.login(username="user", password="123")
        url = reverse('convention:user_profile')
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Profile</a></li>' % url, 'a href="#">Account</a', '/ul')

    def test_account_menu_contains_profile_with_staff(self):
        self.client.login(username="staff", password="123")
        url = reverse('convention:user_profile')
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Profile</a></li>' % url, 'a href="#">Account</a', '/ul')

    def test_account_menu_contains_profile_with_admin(self):
        self.client.login(username="admin", password="123")
        url = reverse('convention:user_profile')
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">Profile</a></li>' % url, 'a href="#">Account</a', '/ul')

    def test_account_menu_contains_logout_with_user(self):
        self.client.login(username="user", password="123")
        url = reverse('logout')
        text = "Logout"
        menu_start = 'a href="#">Account</a'
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">%s</a></li>' % (url, text), menu_start, '/ul')

    def test_account_menu_contains_logout_with_staff(self):
        self.client.login(username="staff", password="123")
        url = reverse('logout')
        text = "Logout"
        menu_start = 'a href="#">Account</a'
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">%s</a></li>' % (url, text), menu_start, '/ul')

    def test_account_menu_contains_logout_with_admin(self):
        self.client.login(username="admin", password="123")
        url = reverse('logout')
        text = "Logout"
        menu_start = 'a href="#">Account</a'
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">%s</a></li>' % (url, text), menu_start, '/ul')

    def test_account_menu_no_admin_with_user(self):
        self.client.login(username="user", password="123")
        url = reverse('admin:index')
        text = "Admin"
        menu_start = 'a href="#">Account</a'
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">%s</a></li>' % (url, text), menu_start, '/ul', False)

    def test_account_menu_contains_admin_with_staff(self):
        self.client.login(username="staff", password="123")
        url = reverse('admin:index')
        text = "Admin"
        menu_start = 'a href="#">Account</a'
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">%s</a></li>' % (url, text), menu_start, '/ul')

    def test_account_menu_contains_admin_with_admin(self):
        self.client.login(username="admin", password="123")
        url = reverse('admin:index')
        text = "Admin"
        menu_start = 'a href="#">Account</a'
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<li><a href="%s">%s</a></li>' % (url, text), menu_start, '/ul')

    # #################################################################
    # ########################## Side Bar #############################
    # #################################################################

    # ########################## Registration #############################
    def test_date_show_before_registration_opens(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = pytz.timezone("US/Pacific").localize(datetime(3000, 1, 10, 02, 59, 58))
        info.save()
        pattern = "<h3>Registration Opens:</h3>\\s+<ul><li>January 10th, 3000<br>2:59:58 AM PST</li></ul>"
        response = self.client.get(self.url)
        self.assertSectionContains(response, pattern, "aside", 'li id="deadlines"')

    def test_date_show_before_registration_opens_alternate(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = pytz.timezone("US/Pacific").localize(datetime(2037, 6, 3, 22, 27, 42))
        info.save()
        pattern = "<h3>Registration Opens:</h3>\\s+<ul><li>June 3rd, 2037<br>10:27:42 PM PDT</li></ul>"
        response = self.client.get(self.url)
        self.assertSectionContains(response, pattern, "aside", 'li id="deadlines"')

    def test_date_registration_links_after_open(self):
        info = ConInfo.objects.all()[0]
        info.registration_opens = timezone.now()
        info.save()
        pattern = '<li><a href="%s">%s</a></li>'
        response = self.client.get(self.url)
        self.assertSectionContains(response,
                                   pattern % (reverse("convention:register_attendance"), "Register Attendance"),
                                   "aside",
                                   'li id="deadlines"')
        self.assertSectionContains(response, pattern % (reverse("convention:submit_game"), "Submit Game"), "aside",
                                   'li id="deadlines"')

    def test_sidebar_game_registration_link_with_registration(self):
        self.client.login(username="admin", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response,
                                   '<li><a href="https://goo.gl/forms/xKWoC8boOUIFi32U2">Game Registration</a></li>',
                                   "aside",
                                   'li id="deadlines"')

    def test_sidebar_game_registration_link_with_no_user(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response,
                                   '<li><a href="https://goo.gl/forms/xKWoC8boOUIFi32U2">Game Registration</a></li>',
                                   "aside",
                                   'li id="deadlines"',
                                   expected=False)

    def test_sidebar_game_registration_link_with_no_registration(self):
        self.client.login(username="user", password="123")
        response = self.client.get(self.url)
        self.assertSectionContains(response,
                                   '<li><a href="https://goo.gl/forms/xKWoC8boOUIFi32U2">Game Registration</a></li>',
                                   "aside",
                                   'li id="deadlines"',
                                   expected=False)

    # ########################## Deadlines #############################

    def test_pre_reg_deadline(self):
        pattern = '<li>%s<br/>\\s+<ul>\\s+<li>%s</li>\\s+</ul>\\s+</li>' % ("Pre-Registration:", "March 15th, 2016")
        response = self.client.get(self.url)
        self.assertSectionContains(response, pattern, 'li id="deadlines"', '/aside')

    def test_pre_reg_deadline_alternate(self):
        info = ConInfo.objects.all()[0]
        info.pre_reg_deadline = date(2017, 7, 3)
        info.save()
        pattern = '<li>%s<br/>\\s+<ul>\\s+<li>%s</li>\\s+</ul>\\s+</li>' % ("Pre-Registration:", "July 3rd, 2017")
        response = self.client.get(self.url)
        self.assertSectionContains(response, pattern, 'li id="deadlines"', '/aside')

    def test_game_submission_deadline(self):
        pattern = '<li>%s<br/>\\s+<ul>\\s+<li>%s</li>\\s+</ul>\\s+</li>' % ("Game Submission:", "March 22nd, 2016")
        response = self.client.get(self.url)
        self.assertSectionContains(response, pattern, 'li id="deadlines"', '/aside')

    def test_game_submission_deadline_alternate(self):
        info = ConInfo.objects.all()[0]
        info.game_sub_deadline = date(3001, 12, 8)
        info.save()
        pattern = '<li>%s<br/>\\s+<ul>\\s+<li>%s</li>\\s+</ul>\\s+</li>' % ("Game Submission:", "December 8th, 3001")
        response = self.client.get(self.url)
        self.assertSectionContains(response, pattern, 'li id="deadlines"', '/aside')

    def test_game_registration_deadline(self):
        pattern = '<li>%s<br/>\\s+<ul>\\s+<li>%s</li>\\s+</ul>\\s+</li>' % ("Game Registration:",
                                                                            "September 15th, 2016<br />6:00:00 PM PDT")
        response = self.client.get(self.url)
        self.assertSectionContains(response, pattern, 'li id="deadlines"', '/aside')

    def test_game_registration_deadline_alternate(self):
        info = ConInfo.objects.all()[0]
        info.game_reg_deadline = pytz.timezone("US/Pacific").localize(datetime(3002, 12, 18, 13, 33, 14))
        info.save()
        pattern = '<li>%s<br/>\\s+<ul>\\s+<li>%s</li>\\s+</ul>\\s+</li>' % ("Game Registration:",
                                                                            "December 18th, 3002<br />1:33:14 PM PST")
        response = self.client.get(self.url)
        self.assertSectionContains(response, pattern, 'li id="deadlines"', '/aside')

    # #################################################################
    # ########################## Side Bar #############################
    # #################################################################

    def test_contact_us_link(self):
        response = self.client.get(self.url)
        self.assertSectionContains(response, '<a href="' + reverse('contact:contact') + '">Contact Us</a>', 'footer')


class AlternatePageTemplateTest(BaseTemplateTest):
    url = reverse('contact:contact')
