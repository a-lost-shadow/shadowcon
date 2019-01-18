from django import template

from ..models import Game
from ..utils import get_current_con

register = template.Library()


@register.inclusion_tag('convention/user_games_list.html')
def show_user_games(user=None):
    convention = get_current_con()
    return {'games': Game.objects.filter(user=user).filter(convention=convention)}
