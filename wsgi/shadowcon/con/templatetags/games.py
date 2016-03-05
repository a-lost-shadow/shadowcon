from django import template

from collections import OrderedDict

from ..models import Game, Location

register = template.Library()
offsets = {u'friday': -18,
           u'saturday': 6,
           u'sunday': 30,
           }

row_height = 30
game_height = row_height - 3
total = {"width": 700}
hour = {"width": 12.5, "offset": 14}
hour["block_width"] = 4 * hour["width"]
grid = {"x": 106, "y": 40, "width": hour["width"] * 46,
        "light": {"x": 0, "y": 0}}
grid["bold"] = {"x": grid["x"] % (4 * hour["width"]) - 2 * hour["width"] - 1,
                "y": grid["y"] % row_height}
days = {"x": grid["x"] + 6 * hour["width"] - 1, "y": 10, "height": 20, "width": hour["block_width"] * 6}
hour_header = {"y": 35, "offset": 11}
day_header = {"y": 15,
              "friday": grid["x"] + 6 * hour["width"] - 76,
              "saturday": grid["x"] + 18 * hour["width"] - hour_header["offset"] - 20,
              "sunday": grid["x"] + 36 * hour["width"] - hour_header["offset"] + 30,
              }
text_offset = 4


@register.inclusion_tag('con/user_games_list.html')
def show_user_games(user, registration_open):
    return {'games': Game.objects.filter(user=user),
            'registration_open': registration_open}


class ScheduleGameBlock:
    def __init__(self, game):
        self.game = game

        self.x = offsets.get(unicode(game.time_block.first_word().lower()), 100) + game.time_slot.start
        self.x *= hour["width"]
        self.x += grid["x"]
        self.text = {"x": self.x + text_offset}

        self.width = game.time_slot.stop - game.time_slot.start
        if self.width < 0:
            self.width += 24
        self.width = self.width * hour["width"] - 1


class ScheduleLocationBlock:
    def __init__(self, location, row_counter):
        self.games = map(lambda x: ScheduleGameBlock(x), Game.objects.filter(location=location))
        self.row = row_counter.increment_and_get()
        self.text = {"x": text_offset, "y": 61 + row_height * self.row, "value": location.text}
        self.game_offset = 42 + row_height * self.row


class Counter:
    def __init__(self):
        self.count = -1

    def increment_and_get(self):
        self.count += 1
        return self.count

    def get(self):
        return self.count


def am_pm_print(value):
    if 0 == value:
        return "12am"
    if 12 == value:
        return "12pm"
    if value < 12:
        return "%dam" % value
    else:
        return "%dpm" % (value - 12)


@register.inclusion_tag('con/location_schedule.html')
def location_schedule():
    row_counter = Counter()
    locations = map(lambda x: ScheduleLocationBlock(x, row_counter), Location.objects.all())
    total["height"] = 71 + row_counter.get() * row_height

    hour_headers = OrderedDict()
    for h in range(2, 47, 4):
        hour_headers[grid["x"] - hour_header["offset"] + hour["width"] * h] = am_pm_print((h + 18) % 24)
    print grid["bold"]

    return {'locations': locations,
            'hour': hour,
            'grid': grid,
            'total': total,
            'hour_header': hour_header,
            'day_header': day_header,
            'row_height': row_height,
            'hour_headers': hour_headers,
            'days': days,
            'game_height': game_height,
            }
