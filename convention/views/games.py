from django_ajax.mixin import AJAXMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils import timezone
from django.views import generic
from reversion import revisions as reversion

from collections import OrderedDict

from ..models import Game, GamePlayer, Location, TimeBlock, TimeSlot
from ..utils import friendly_username, get_current_con
from .common import ConHasSpaceOrAlreadyRegisteredMixin, IsStaffMixin, RevisionMixin
from contact.utils import mail_list

game_fields = ['title', 'gm', 'game_length', 'number_players', 'system', 'triggers', 'preferred_time',
               'special_requests', 'description']


def get_games():
    convention = get_current_con()
    return Game.objects.filter(convention=convention).order_by('time_block', 'time_slot', 'title')


def get_games_for_user(user):
    convention = get_current_con()
    return map(
        lambda game: {
            "game": game,
            "players": User.objects.filter(gameplayer__game=game)
        },
        Game.objects.filter(gameplayer__player=user, convention=convention).order_by('time_block', 'time_slot', 'title')
    )


class ScheduleData:
    by_time_block = OrderedDict()
    user_games = []
    in_games = False


class ScheduleView(generic.ListView):
    template_name = 'convention/game_schedule_view.html'

    def get_queryset(self):
        gamedata = ScheduleData()
        gamedata.by_time_block = OrderedDict()
        gamedata.user_games = get_games_for_user(self.request.user)
        gamedata.in_games = len(gamedata.user_games) > 0

        for game in get_games():
            time_block = game.friendly_block()
            if time_block not in gamedata.by_time_block:
                gamedata.by_time_block[time_block] = []
            gamedata.by_time_block[time_block].append(game)

        return gamedata


class ScheduleEditView(LoginRequiredMixin, IsStaffMixin, generic.TemplateView):
    template_name = 'convention/game_schedule_edit.html'


class NewGameView(LoginRequiredMixin, ConHasSpaceOrAlreadyRegisteredMixin, generic.CreateView):
    model = Game
    fields = game_fields
    waiting_list_template = 'convention/game_submission_wait_list.html'

    def get_success_url(self):
        return reverse('convention:user_profile')

    def get_initial(self):
        initial = super(NewGameView, self).get_initial()
        initial.update({'gm': friendly_username(self.request.user)})
        return initial

    def send_email(self):
        subject_details = "%s submitted '%s'" % (friendly_username(self.request.user), self.object.title)
        message = self.object.email_format(self.request)
        mail_list("Game Submission", subject_details, message, list_name="game_submission")

    def form_valid(self, form):
        # since the form doesn't have the user, time or convention, we need to insert them
        form.instance.user = self.request.user
        form.instance.last_modified = timezone.now()
        form.instance.convention = get_current_con()

        with reversion.create_revision():
            reversion.set_user(self.request.user)
            reversion.set_comment("Form Submission - New")

            result = super(NewGameView, self).form_valid(form)
        self.send_email()
        return result


class UpdateGameView(LoginRequiredMixin, ConHasSpaceOrAlreadyRegisteredMixin, RevisionMixin, generic.UpdateView):
    model = Game
    fields = game_fields
    waiting_list_template = 'convention/game_submission_wait_list.html'
    revision_log_prefix = "Form Submission"
    changed_ignore_list = ["last_modified"]

    def get_success_url(self):
        return reverse('convention:user_profile')

    def form_valid(self, form):
        if self.request.user != self.object.user:
            return render(self.request, 'convention/not_game_owner.html', {})

        form.instance.last_modified = timezone.now()
        return super(UpdateGameView, self).form_valid(form)

    def get(self, request, *args, **kwargs):
        if request.user == self.get_object().user:
            return super(UpdateGameView, self).get(self, request, *args, **kwargs)
        else:
            return render(request, 'convention/not_game_owner.html', {})


class ListGameView(generic.ListView):
    model = Game

    def get_queryset(self):
        return get_games()


offsets = {u'friday': -18,
           u'saturday': 6,
           u'sunday': 30,
           }


def get_block_offset(time_block):
    offset = offsets.get(unicode(time_block.first_word().lower()), 100)
    if time_block.has_second_word() and "midnight" == time_block.second_word().lower():
        offset += 24
    return offset


def get_start(game):
    if game.time_block and game.time_slot:
        return get_block_offset(game.time_block) + game.time_slot.start
    else:
        return 100


def get_width(time_slot):
    if time_slot:
        width = time_slot.stop - time_slot.start
        if width < 0:
            width += 24
        return width
    else:
        return 0


def get_index(obj, object_list):
    if object_list.count(obj):
        return object_list.index(obj)
    else:
        return -1


class SchedulerHandler(AJAXMixin, generic.base.View):
    def get(self, request, *args, **kwargs):
        convention = get_current_con()
        locations = map(lambda x: x, Location.objects.filter(convention = convention))
        blocks = map(lambda x: x, TimeBlock.objects.all().order_by('sort_id'))
        slots = map(lambda x: x, TimeSlot.objects.all().order_by('start'))
        games = get_games()

        return {"locations": map(lambda x: {"text": x.text, "id": x.id}, locations),
                "games": map(lambda x: {"title": x.title,
                                        "id": x.id,
                                        "gm": x.gm,
                                        "location": get_index(x.location, locations),
                                        "time_block": get_index(x.time_block, blocks),
                                        "time_slot": get_index(x.time_slot, slots),
                                        "preferred_time": x.preferred_time,
                                        "special_requests": x.special_requests,
                                        "start": get_start(x),
                                        "width": get_width(x.time_slot),
                                        },
                             games),
                "blocks": map(lambda x: {"text": x.text, "id": x.id, "offset": get_block_offset(x)}, blocks),
                "slots": map(lambda x: {"text": str(x), "id": x.id, "start": x.start, "width": get_width(x)}, slots),
                }

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Exception("Not logged in!  Only staff have access to this function")

        if not request.user.is_staff and not request.user.is_superuser:
            raise Exception("Only staff have access to this function")

        keys = [('location', Location), ('time_block', TimeBlock), ('time_slot', TimeSlot)]
        key_text = 0
        key_db_object = 1

        game_id = request.POST.get('id')
        game = Game.objects.get(id=game_id)

        changed = []

        for key in keys:
            incoming_id = request.POST.get(key[key_text])
            old = getattr(game, key[key_text])
            new = key[key_db_object].objects.get(id=incoming_id) if incoming_id else None

            setattr(game, key[key_text], new)
            if old != new:
                changed.append(key[key_text])

        changed.sort()
        game.last_scheduled = timezone.now()

        with reversion.create_revision():
            reversion.set_user(request.user)
            reversion.set_comment("AJAX Schedule Submission - %s Changed" % ", ".join(changed))

            game.save()
