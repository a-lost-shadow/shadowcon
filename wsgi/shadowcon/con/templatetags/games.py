from django import template

from ..models import Game

register = template.Library()


@register.inclusion_tag('con/user_games_list.html')
def show_user_games(user=None):
    return {'games': Game.objects.filter(user=user)}
