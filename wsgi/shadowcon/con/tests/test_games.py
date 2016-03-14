from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory, Client
from ..models import Game


class SimpleTest(TestCase):
    fixtures = ['auth', 'initial']

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.client = Client()

    def test_cannot_modify_other_games_get(self):
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('con:edit_game', args=[game.id])

        self.client.login(username='adrian', password='123')
        response = self.client.get(url)
        self.assertContains(response, "<h2>Cannot edit another's game</h2>")

    def test_cannot_modify_other_games_post(self):
        user = User.objects.get(username='staff')
        game = Game.objects.filter(user=user)[0]
        url = reverse('con:edit_game', args=[game.id])

        self.client.login(username='adrian', password='123')
        original_title = game.title
        game.title = 'Changed Via Unit Test'

        response = self.client.post(url, game.__dict__)
        self.assertEqual(original_title, Game.objects.get(id=game.id).title)
        self.assertContains(response, "<h2>Cannot edit another's game</h2>")

    def test_modify_without_login_redirects(self):
        game = Game.objects.all()[0]
        url = reverse('con:edit_game', args=[game.id])
        login_url = reverse('login')

        response = self.client.post(url, game.__dict__)
        self.assertRedirects(response, login_url + "?next=" + url)
