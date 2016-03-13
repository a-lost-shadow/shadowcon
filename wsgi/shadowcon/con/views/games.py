from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.views import generic
from django.utils import timezone
from django_ajax.mixin import AJAXMixin

from collections import OrderedDict

from ..models import Game, Location, TimeBlock, TimeSlot
from ..utils import friendly_username
from .common import RegistrationOpenMixin, NotOnWaitingListMixin, IsStaffMixin
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


class ScheduleEditView(LoginRequiredMixin, IsStaffMixin, generic.TemplateView):
    template_name = 'con/game_schedule_edit.html'


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


def get_block_offset(time_block):
    offset = offsets.get(unicode(time_block.first_word().lower()), 100)
    if "midnight" == time_block.second_word().lower():
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
        locations = map(lambda x: x, Location.objects.all())
        blocks = map(lambda x: x, TimeBlock.objects.all().order_by('sort_id'))
        slots = map(lambda x: x, TimeSlot.objects.all().order_by('start'))
        games = Game.objects.all()

        return {"locations": map(lambda x: {"text": x.text, "id": x.id}, locations),
                "games": map(lambda x: {"title": x.title,
                                        "id": x.id,
                                        "gm": x.gm,
                                        "location": get_index(x.location, locations),
                                        "time_block": get_index(x.time_block, blocks),
                                        "time_slot": get_index(x.time_slot, slots),
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

        game_id = request.POST.get('id')
        location_id = request.POST.get('location')
        time_block_id = request.POST.get('time_block')
        time_slot_id = request.POST.get('time_slot')

        game = Game.objects.get(id=game_id)
        if location_id:
            game.location = Location.objects.get(id=location_id)
        else:
            game.location = None

        if time_block_id:
            game.time_block = TimeBlock.objects.get(id=time_block_id)
        else:
            game.time_block = None

        if time_slot_id:
            game.time_slot = TimeSlot.objects.get(id=time_slot_id)
        else:
            game.time_slot = None

        game.last_scheduled = timezone.now()
        game.save()
