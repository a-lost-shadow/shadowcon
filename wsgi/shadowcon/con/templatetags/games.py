from django import template

from ..models import Game

register = template.Library()


@register.inclusion_tag('con/user_games_list.html')
def show_user_games(user, registration_open):
    return {'games': Game.objects.filter(user=user),
            'registration_open': registration_open}
