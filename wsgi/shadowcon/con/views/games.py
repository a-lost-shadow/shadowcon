from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.views import generic
from django.utils import timezone
from django_ajax.decorators import ajax

from collections import OrderedDict

from ..models import Game, Location
from ..utils import friendly_username
from .common import RegistrationOpenMixin, NotOnWaitingListMixin
from contact.utils import mail_list

game_fields = ['title', 'gm', 'duration', 'number_players', 'system', 'triggers', 'description']


def get_games():
    return Game.objects.order_by('time_block', 'time_slot', 'title')


class ScheduleView(generic.ListView):
    template_name = 'con/game_schedule_view.html'

    def get_queryset(self):
        game_map = OrderedDict()
        for game in get_games():
            time_block = game.friendly_block()
            if time_block not in game_map:
                game_map[time_block] = []
            game_map[time_block].append(game)

        return game_map


class NewGameView(RegistrationOpenMixin, LoginRequiredMixin, NotOnWaitingListMixin, generic.CreateView):
    model = Game
    fields = game_fields
    waiting_list_template = 'con/game_submission_wait_list.html'

    def get_success_url(self):
        return reverse('con:user_profile')

    def get_initial(self):
        initial = super(NewGameView, self).get_initial()
        initial.update({'gm': friendly_username(self.request.user)})
        return initial

    def send_email(self):
        subject_details = "%s submitted '%s'" % (friendly_username(self.request.user), self.object.title)
        message = self.object.email_format(self.request)
        mail_list("Game Submission", subject_details, message, "no-reply@shadowcon.net", list_name="game_submission")

    def form_valid(self, form):
        # since the form doesn't have the user or time, we need to insert it
        form.instance.user = self.request.user
        form.instance.last_modified = timezone.now()
        result = super(NewGameView, self).form_valid(form)
        self.send_email()
        return result


class UpdateGameView(RegistrationOpenMixin, LoginRequiredMixin, NotOnWaitingListMixin, generic.UpdateView):
    model = Game
    fields = game_fields
    waiting_list_template = 'con/game_submission_wait_list.html'

    def get_success_url(self):
        return reverse('con:user_profile')

    def form_valid(self, form):
        form.instance.last_modified = timezone.now()
        return super(UpdateGameView, self).form_valid(form)


class ListGameView(generic.ListView):
    model = Game

    def get_queryset(self):
        return get_games()


offsets = {u'friday': -18,
           u'saturday': 6,
           u'sunday': 30,
           }


def get_start(game):
    return offsets.get(unicode(game.time_block.first_word().lower()), 100) + game.time_slot.start


def get_width(game):
    width = game.time_slot.stop - game.time_slot.start
    if width < 0:
        width += 24
    return width


@ajax
def location_schedule_view(request):
    locations = map(lambda x: x, Location.objects.exclude(text__startswith='Not'))
    games = Game.objects.filter(location__in=locations).filter(time_block__isnull=False).filter(time_slot__isnull=False)

    return {"locations": map(lambda x: x.text, locations),
            "games": map(lambda x: {"title": x.title,
                                    "location": locations.index(x.location),
                                    "start": get_start(x),
                                    "width": get_width(x),
                                    },
                         games),
            }
