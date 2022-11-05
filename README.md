# Django Compose Tag

[![ci-status-image]][ci-status]
[![pypi-version]][pypi]

**Compose templates easily**

Django Compose tags provide the tags to ease templates composition, 
with an api close to the `include` template tag.

The api is thought to ease the implementation and usage of design systems in django.  

---

# Overview

Write your template as you would for the `include` tag:

```jinja
<!-- card.html -->

<article class="card">
    <div class="card-body">{{ children }}</div>
    <footer class="card-footer">{{ footer }}</footer>
</article>
```

## The `compose` tag

The `compose` template tag behave similarly to [django's `include`][django-include-doc].
The main difference is that the content between `{% compose %}` and `{% endcompose %}` is regular django template that's accessible withing the composed template as the `{{ children }}` variable.

```jinja
{% load compose %}

{% compose "card.html" footer="My footer" %}
    <p>card.html receive this as the {{ children }} variable</p>
    <p>You can use {{ context_varialbe }} in here.</p>
{% endcompose %}
```

By default the composed template doesn't have access to the context, if you need access to the context set the takes_context option `{% compose "card.html" takes_context %}`. `takes_context` is the opposite of the `only` 

## The `define` tag

### define

The `define` template tag allows you to set a new variable from within a template. That's a convenient way to use template rendered variables for any tag parameter.

```jinja
{% define mylink %}<a href={{ link.url }}>Go to {{ link.name }}{% enddefine %}

{% include "card.html" children="Card body" footer=mylink %}
{% compose "card.html" footer=mylink %}
Card body with {{ context_variable }}
{% endcompose %}
```

## Custom composition tag

`composition_tag` is to `compose` what [`inclustion_tag`][django-inclusiontag-doc] is to the `include` tag.

Define you tag function and decorate it with `composition_tag`, the decorator takes care of passing the children as the first argument of your custom tag.

```python
# mydesignsystem/templatetags/mydesignsystem.py

from django.template import Library
from compose_tags import composition_tag

register = Library()

@register.tag
@composition_tag('card.html', takes_context=True)
def card(children, context, next, cancelable=False):
    return {
        "children": children,
        "footer": create_footer(next, cancelable),
    }
```

Then use it in your templates, by default the tag is named after your function name.

```jinja
{% load mydesignsystem %}

{% card next=someurl cancelable=True %}My card children{% endcard %}
```

### Declaring composition_tag

There are multiple ways to use composition_tag. The first is as a decorator:

```python
@register.tag
@composition_tag('template.html')
def mytag(children, **kwargs):
    # Usage: {% mytag %}children{% endmytag %} 
    ...

@register.tag("customname")
@composition_tag('template.html')
def mytag(children, **kwargs):
    # Usage: {% customname %}children{% endcustomname %} 
    ...
```

When you don't need to do any python processing, there is a default implementation that forward all parameters as is.
When you rely on that default implementation the default tag name is derived from the template name.

Which mean `register.tag(composition_tag("button.html"))` is equivalent to
```python
@register.tag
@composition_tag('button.html')
def button(children, **kwargs):
    return {
        **kwargs,
        "children": children
    }
```

As with the decorator usage, you can override the tag name: `register.tag("mybutton", composition_tag("button.html"))`

----

# Requirements

* Python (3.6, 3.7, 3.8, 3.9, 3.10, 3.11)
* Django (2.2, 3.0, 3.1, 3.2, 4.0, 4.1)

We **highly recommend** and only officially support the latest patch release of
each Python and Django series.

# Installation

Install using `pip install django-compose-tags`

Add `'compose_tags'` to your `INSTALLED_APPS` setting.
```python
INSTALLED_APPS = [
    ...
    'compose_tags',
]
```

If you use `compose` a lot we recommend you add it to your builtins:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            # ...
            "builtins": ["compose_tags.templatetags.compose"],
        }
    }
]
```

---

# Alternatives

Django Compose Tag purposely provide a simple api based solely on templates.

If Django Compose Tag doesn't cover your requirements we recommend you take a look at [jinja][jinja-homepage].

[ci-status-image]: https://github.com/HelloWatt/django-compose-tags/actions/workflows/main.yml/badge.svg
[ci-status]: https://github.com/HelloWatt/django-compose-tags/actions/workflows/main.yml
[pypi-version]: https://img.shields.io/pypi/v/django-compose-tags.svg
[pypi]: https://pypi.org/project/django-compose-tags/


[jinja-homepage]: https://jinja.palletsprojects.com
[django-include-doc]: https://docs.djangoproject.com/en/dev/ref/templates/builtins/#include
[django-inclusiontag-doc]: https://docs.djangoproject.com/en/dev/howto/custom-template-tags/#inclusion-tags