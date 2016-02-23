from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.core.urlresolvers import reverse

from collections import OrderedDict

from ..models import Game
from ..utils import friendly_username

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


class NewGameView(LoginRequiredMixin, generic.CreateView):
    model = Game
    fields = game_fields

    def get_success_url(self):
        return reverse('con:user_profile')

    def get_initial(self):
        initial = super(NewGameView, self).get_initial()
        initial.update({'gm': friendly_username(self.request.user)})
        return initial

    def form_valid(self, form):
        # since the form doesn't have the user, we need to insert it
        form.instance.user = self.request.user
        return super(NewGameView, self).form_valid(form)


class UpdateGameView(LoginRequiredMixin, generic.UpdateView):
    model = Game
    fields = game_fields

    def get_success_url(self):
        return reverse('con:user_profile')


class ListGameView(generic.ListView):
    model = Game

    def get_queryset(self):
        return get_games()