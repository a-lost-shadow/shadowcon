from django.template import Template, Context

import re

from .models import Tag

tag_pattern = "\{[ \t]*\{[ \t]*%s[ \t]*\}[ \t]*\}"


def replace_tags(text):
    for tag in Tag.objects.all():
        pattern = tag_pattern % tag.tag
        if re.search(pattern, text):
            expanded = Template(tag.content).render(Context({}))
            text = re.sub(tag_pattern % tag.tag, expanded, text)
    return text
