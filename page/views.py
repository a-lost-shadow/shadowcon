from django.shortcuts import render, get_object_or_404
from .models import Page
from .utils import replace_tags


def index(request):
    return display(request, 'home')


def display(request, url):
    url = url.replace("/", "_")
    page = get_object_or_404(Page, url=url)
    title = "- " + page.name

    if "home" == url:
        title = ""

    context = {'title': title, 'content': replace_tags(page.content)}
    return render(request, 'page/display.html', context)
