from ddt import data, ddt
from django.http.request import HttpRequest
from django.test.utils import override_settings
from django.utils.html import strip_tags
from shadowcon.tests.utils import ShadowConTestCase
from ..models import ConInfo, Game, BlockRegistration, TimeBlock, TimeSlot, PaymentOption, Registration, Location
from ..models import get_absolute_url, am_pm_print
from ..utils import get_choice


@ddt
class ModelsTest(ShadowConTestCase):
    @override_settings(DEBUG=False)
    def test_abs_url_no_debug(self):
        request = HttpRequest()
        request.META['SERVER_NAME'] = 'www.server-name.com'
        request.META['SERVER_PORT'] = '80'
        self.assertEquals('http://www.shadowcon.net/user/payment/',
                          get_absolute_url(request, "con:payment", args=()))

    @override_settings(DEBUG=False)
    def test_abs_url_no_debug_with_arg(self):
        request = HttpRequest()
        request.META['SERVER_NAME'] = 'www.server-name.com'
        request.META['SERVER_PORT'] = '80'
        self.assertEquals('http://www.shadowcon.net/admin/con/game/17/change/',
                          get_absolute_url(request, "admin:con_game_change", args=(17,)))

    @override_settings(DEBUG=True)
    def test_abs_url_debug(self):
        request = HttpRequest()
        request.META['SERVER_NAME'] = 'www.server-name.com'
        request.META['SERVER_PORT'] = '80'
        self.assertEquals('http://www.server-name.com/user/payment/',
                          get_absolute_url(request, "con:payment", args=()))

    CHOICE_1 = '1'
    CHOICE_2 = 'Hmm'
    CHOICE_3 = '_3'

    CHOICES = (
        (CHOICE_1, 'First'),
        (CHOICE_2, '2nd'),
        (CHOICE_3, '3rd'),
    )

    def test_get_choice_1(self):
        self.assertEquals('First', get_choice(self.CHOICE_1, self.CHOICES))

    def test_get_choice_2(self):
        self.assertEquals('2nd', get_choice(self.CHOICE_2, self.CHOICES))

    def test_get_choice_3(self):
        self.assertEquals('3rd', get_choice(self.CHOICE_3, self.CHOICES))

    def test_get_choice_bad(self):
        with self.assertRaises(ValueError) as e:
            get_choice('something else', self.CHOICES)
        self.assertEquals(e.exception.message, "No choice found for: something else")

    def test_con_info_string(self):
        item = ConInfo.objects.all()[0]
        string = str(item)
        self.assertTrue("Date: %s" % item.date in string)
        self.assertTrue("Location: %s" % item.location in string)
        self.assertTrue("Game Submission Deadline: %s" % item.game_sub_deadline in string)
        self.assertTrue("PreReg Deadline: %s" % item.pre_reg_deadline in string)
        self.assertTrue("PreReg Cost: %s" % item.pre_reg_cost in string)
        self.assertTrue("Door Cost: %s" % item.door_cost in string)
        self.assertTrue("Registration Opens: %s" % item.registration_opens in string)
        self.assertTrue("Max Attendees: %s" % item.max_attendees in string)

    def test_time_block_first_word(self):
        item = TimeBlock(text="Word Separation Test", sort_id=1)
        self.assertEquals("Word", item.first_word())

    def test_time_block_first_word_alternate(self):
        item = TimeBlock(text="Alternate Word Separation Test", sort_id=1)
        self.assertEquals("Alternate", item.first_word())

    def test_time_block_second_word(self):
        item = TimeBlock(text="Word Separation Test", sort_id=1)
        self.assertEquals("Separation", item.second_word())

    def test_time_block_second_word_alternate(self):
        item = TimeBlock(text="Alternate Word Separation Test", sort_id=1)
        self.assertEquals("Word", item.second_word())

    def test_time_block_has_second_word(self):
        item = TimeBlock(text="Word Separation Test", sort_id=1)
        self.assertEquals(True, item.has_second_word())

    def test_time_block_no_second_word(self):
        item = TimeBlock(text="Alternate", sort_id=1)
        self.assertEquals(False, item.has_second_word())

    def test_time_bock_string(self):
        item = TimeBlock(text="Word Separation Test", sort_id=1)
        self.assertEquals("Word Separation Test[1]", str(item))

    def test_time_block_string_alternate(self):
        item = TimeBlock(text="Alternate Word Separation Test", sort_id=5)
        self.assertEquals("Alternate Word Separation Test[5]", str(item))

    @data('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    def test_time_block_combined(self, day):
        item = TimeBlock(text=day + " Test", sort_id=1)
        slot = TimeSlot(start=2, stop=4)

        self.assertEquals(day + " 2 AM - 4 AM", item.get_combined(slot))

    def test_time_block_combined_case_insensitive(self):
        item = TimeBlock(text="MONDaY Test", sort_id=1)
        slot = TimeSlot(start=2, stop=4)

        self.assertEquals("MONDaY 2 AM - 4 AM", item.get_combined(slot))

    def test_time_block_combined_case_non_day(self):
        item = TimeBlock(text="FooBar Test", sort_id=1)
        slot = TimeSlot(start=2, stop=4)

        self.assertEquals("FooBar Test : 2 AM - 4 AM", item.get_combined(slot))

    def test_am_pm_print_midnight(self):
        self.assertEquals("Midnight", am_pm_print(0))

    def test_am_pm_print_noon(self):
        self.assertEquals("Noon", am_pm_print(12))

    @data(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
    def test_am_pm_print_am(self, value):
        self.assertEquals("%d AM" % value, am_pm_print(value))

    @data(13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
    def test_am_pm_print_pm(self, value):
        self.assertEquals("%d PM" % (value - 12), am_pm_print(value))

    def test_time_slot_string(self):
        self.assertEquals("4 AM - Noon", str(TimeSlot(start=4, stop=12)))

    def test_location_string(self):
        self.assertEquals("Test Location", str(Location(text="Test Location")))

    def test_location_string_alternate(self):
        self.assertEquals("Alternate", str(Location(text="Alternate")))

    def check_game_string(self, string, game):
        self.assertTrue("Title: %s" % game.title in string)
        self.assertTrue("GM: %s" % game.gm in string)
        self.assertTrue("Number Players: %s" % game.number_players in string)
        self.assertTrue("Duration: %s" % game.duration in string)
        self.assertTrue("System: %s" % game.system in string)
        self.assertTrue("Triggers: %s" % game.triggers in string)

    def test_game_string(self):
        game = Game.objects.all()[0]
        game_str = str(game)
        self.check_game_string(game_str, game)
        self.assertTrue("Time Block: %s" % game.time_block in game_str)
        self.assertTrue("Time Slot: %s" % game.time_slot in game_str)
        self.assertTrue("Location: %s" % game.location in game_str)
        self.assertTrue("User: %s" % game.user in game_str)
        self.assertTrue("Last Modified: %s" % game.last_modified in game_str)
        self.assertTrue("Last Scheduled: %s" % game.last_scheduled in game_str)

    @override_settings(DEBUG=False)
    def test_game_email(self):
        game = Game.objects.all()[0]
        game_str = str(game.email_format(None))
        self.assertTrue("HTML Description:\n%s" % game.description in game_str)
        self.assertTrue("Raw Description:\n%s" % strip_tags(game.description) in game_str)
        self.assertTrue("Admin Link:\nhttp://www.shadowcon.net/admin/con/game/%d/change/" % game.id in game_str)

    def test_game_header_target(self):
        game = Game(title="This is a test!")
        self.assertEquals("this_is_a_test_", game.header_target())

    def test_game_header_target_alternate(self):
        game = Game(title="++ALTERNATE_game-title++")
        self.assertEquals("__alternate_game_title__", game.header_target())

    def test_game_friendly_block_with_time_block(self):
        block = TimeBlock(text="Monday Test", sort_id=1)
        game = Game(title="++ALTERNATE_game-title++", time_block=block)
        self.assertEquals("Monday Test", game.friendly_block())

    def test_game_friendly_block_no_block(self):
        game = Game(title="++ALTERNATE_game-title++")
        self.assertEquals("Not Scheduled", game.friendly_block())

    def test_game_combined_time_no_block_no_slot(self):
        game = Game(title="Game")
        self.assertEquals("Not Scheduled", game.combined_time())

    def test_game_combined_time_no_block_with_slot(self):
        slot = TimeSlot(start=14, stop=16)
        game = Game(title="Game", time_slot=slot)
        self.assertEquals("Not Scheduled", game.combined_time())

    def test_game_combined_time_with_block_no_slot(self):
        block = TimeBlock(text="Monday Test", sort_id=1)
        game = Game(title="Game", time_block=block)
        self.assertEquals("Not Scheduled", game.combined_time())

    def test_game_combined_time_with_block_with_slot(self):
        block = TimeBlock(text="Monday Test", sort_id=1)
        slot = TimeSlot(start=14, stop=16)
        game = Game(title="Game", time_block=block, time_slot=slot)
        self.assertEquals("Monday 2 PM - 4 PM", game.combined_time())

    def test_game_user_delete(self):
        game = Game.objects.all()[0]
        game_id = game.id
        game.user.delete()

        games = Game.objects.filter(id=game_id)

        self.assertEquals(0, len(games))

    def test_payment_options_slug(self):
        item = PaymentOption(name="Unit Test", description="For Testing")
        self.assertEquals("", str(item.slug))
        item.save()
        self.assertEquals("unit-test", str(item.slug))

    def test_payment_options_string(self):
        item = PaymentOption(name="Unit Test", description="For Testing")
        self.assertEquals("Unit Test", str(item))

    def test_registration_string(self):
        item = Registration.objects.all()[0]
        string = str(item)
        self.assertTrue("User: %s" % item.user in string)
        self.assertTrue("Registration Date: %s" % item.registration_date in string)
        self.assertTrue("Last Updated: %s" % item.last_updated in string)
        self.assertTrue("Payment: %s" % item.payment in string)
        self.assertTrue("Payment Received: %s" % item.payment_received in string)

    def test_registration_user_delete(self):
        item = Registration.objects.all()[0]
        reg_id = item.id
        item.user.delete()

        items = Registration.objects.filter(id=reg_id)
        self.assertEquals(0, len(items))

    def test_block_registration_string(self):
        item = BlockRegistration.objects.all()[0]
        string = str(item)
        self.assertTrue("Registration: %s" % item.registration in string)
        self.assertTrue("Time Block: %s" % item.time_block in string)
        self.assertTrue("Attendance: %s" % get_choice(item.attendance, BlockRegistration.ATTENDANCE_CHOICES) in string)

    def test_block_registration_user_delete(self):
        item = BlockRegistration.objects.all()[0]
        reg_id = item.id
        item.registration.delete()

        items = Registration.objects.filter(id=reg_id)
        self.assertEquals(0, len(items))
